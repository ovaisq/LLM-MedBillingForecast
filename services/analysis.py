"""Analysis service module - business logic for medical billing forecasting."""

import asyncio
import json
import logging
from typing import Any

from database import insert_data_into_table, get_select_query_result_dicts
from encryption import decrypt_text
from gptutils import prompt_chat
from utils import ts_int_to_dt_obj, serialize_datetime

from app.core.config import settings


# Chunk size for batch processing
NUM_ELEMENTS_CHUNK = 25


async def get_store_icd_cpt_codes(
    patient_id: str,
    patient_document_id: str,
    llm: str,
    analyzed_content: str,
) -> None:
    """Get ICD and CPT codes for the diagnosis and store them.

    Args:
        patient_id: Patient identifier
        patient_document_id: Patient document identifier
        llm: LLM model name used for analysis
        analyzed_content: Decrypted analysis content
    """
    from clincodeutils import (
        extract_icd10_codes,
        extract_cpt_codes,
        extract_hcpcs_codes,
        icd_10_code_details_list,
        lookup_cpt_gpt,
        lookup_hcpcs_gpt,
    )

    prompts = {
        "icd": "What are the ICD codes for this diagnosis? ",
        "cpt": "What are the CPT codes for this diagnosis? ",
        "hcpcs": "What are the HCPCS codes for this diagnosis? ",
        "prescription": "What medication to prescribe for the diagnosis? ",
        "prescription_cpt": "What are the CPT codes for these prescriptions? ",
        "prescription_hcpcs": "What are the HCPCS codes for these prescriptions? ",
    }

    # Adjust prompts if llm is 'meditron'
    if llm == "meditron":
        prompts["prescription_cpt"] = prompts["prescription"]

    async def fetch_code(prompt_key: str, content: str) -> dict[str, Any]:
        return await asyncio.to_thread(prompt_chat, llm, prompts[prompt_key] + content, False)

    # Gather all asynchronous tasks
    icd_obj, cpt_obj, hcpcs_obj, prescription_obj = await asyncio.gather(
        fetch_code("icd", analyzed_content),
        fetch_code("cpt", analyzed_content),
        fetch_code("hcpcs", analyzed_content),
        fetch_code("prescription", analyzed_content),
    )

    prescription_analysis = prescription_obj["analysis"]

    # Further gather tasks for prescriptions
    prescription_cpt_obj, prescription_hcpcs_obj = await asyncio.gather(
        fetch_code("prescription_cpt", prescription_analysis),
        fetch_code("prescription_hcpcs", prescription_analysis),
    )

    icd_10_code_details = icd_10_code_details_list(extract_icd10_codes(icd_obj["analysis"]))
    prescription_cpt_details = lookup_cpt_gpt(extract_cpt_codes(prescription_cpt_obj["analysis"]))
    prescription_hcpcs_details = lookup_hcpcs_gpt(extract_hcpcs_codes(prescription_hcpcs_obj["analysis"]))

    hcpcs_codes = extract_hcpcs_codes(hcpcs_obj["analysis"])

    codes_document = {
        "icd": {
            "timestamp": serialize_datetime(icd_obj["timestamp"]),
            "codes": extract_icd10_codes(icd_obj["analysis"]),
            "details": icd_10_code_details,
        },
        "cpt": {
            "timestamp": serialize_datetime(cpt_obj["timestamp"]),
            "codes": extract_cpt_codes(cpt_obj["analysis"]),
            "details": lookup_cpt_gpt(extract_cpt_codes(cpt_obj["analysis"])),
        },
        "hcpcs": {
            "timestamp": serialize_datetime(hcpcs_obj["timestamp"]),
            "codes": hcpcs_codes,
            "details": lookup_hcpcs_gpt(hcpcs_codes),
        },
        "prescription": {
            "timestamp": serialize_datetime(prescription_obj["timestamp"]),
            "prescriptions": prescription_obj["analysis"],
        },
        "prescription_cpt": {
            "timestamp": serialize_datetime(prescription_cpt_obj["timestamp"]),
            "codes": extract_cpt_codes(prescription_cpt_obj["analysis"]),
            "details": prescription_cpt_details,
        },
        "prescription_hcpcs": {
            "timestamp": serialize_datetime(prescription_hcpcs_obj["timestamp"]),
            "codes": extract_hcpcs_codes(prescription_hcpcs_obj["analysis"]),
            "details": prescription_hcpcs_details,
        },
    }

    codes_data = {
        "timestamp": serialize_datetime(ts_int_to_dt_obj()),
        "patient_id": patient_id,
        "patient_document_id": patient_document_id,
        "codes_document": json.dumps(codes_document),
    }

    insert_data_into_table("patient_codes", codes_data)


def analyze_visit_note(visit_note_id: str) -> bool:
    """Analyze a specific visit note.

    Args:
        visit_note_id: Patient note identifier

    Returns:
        True if analysis was successful, False otherwise
    """
    encrypt_analysis = settings.patient_data_encryption_enabled

    sql_query = """
        SELECT
            patient_id, patient_note_id, patient_note, patient_note ->> 'locality' as patient_locality
        FROM
            patient_notes
        WHERE patient_note_id = %s;
    """

    visit_notes = get_select_query_result_dicts(sql_query, (visit_note_id,))

    for visit_note in visit_notes:
        logging.info(visit_note["patient_note_id"][0:10])
        patient_id = visit_note["patient_id"]
        patient_note_id = visit_note["patient_note_id"]

        # decrypt patient note content
        content = decrypt_text(visit_note["patient_note"]["note"])

        prompt = "What disease does this patient have? P is patient, D is Doctor"
        summarized_obj = prompt_chat("phi4", prompt + content)

        if summarized_obj:
            recommended_diagnosis = decrypt_text(summarized_obj["analysis"])

            # process diagnosis for ICD/CPT codes
            for llm in settings.medllms:
                analyzed_obj = prompt_chat(
                    llm,
                    "Diagnose this patient: " + recommended_diagnosis,
                )

                if not analyzed_obj:
                    return False

                # decrypt analysis result for ICD/CPT processing only
                decrypted_analysis = decrypt_text(analyzed_obj["analysis"])
                asyncio.run(
                    get_store_icd_cpt_codes(
                        patient_id,
                        analyzed_obj["shasum_512"],
                        llm,
                        decrypted_analysis,
                    )
                )

                if not encrypt_analysis:
                    logging.error(
                        "URGENT: Patient Data Encryption disabled! "
                        "If spotted in Production logs, notify immediately!"
                    )

                # construct patient data object for storage
                patient_data_obj = {
                    "schema_version": "4",
                    "llm": llm,
                    "source": "healthcare",
                    "category": "patient",
                    "patient_id": patient_id,
                    "patient_note_id": patient_note_id,
                    "osce_note_summarized": summarized_obj["analysis"],
                    "analysis_document": analyzed_obj["analysis"],
                }

                patient_analysis_data = {
                    "timestamp": analyzed_obj["timestamp"],
                    "patient_document_id": analyzed_obj["shasum_512"],
                    "patient_locality": visit_note["patient_locality"],
                    "patient_id": patient_id,
                    "patient_note_id": patient_note_id,
                    "analysis_document": json.dumps(patient_data_obj),
                }

                insert_data_into_table("patient_documents", patient_analysis_data)
                return True
        else:
            return False

    return False


def analyze_visit_notes() -> bool:
    """Analyze all visit notes in the database.

    Returns:
        True if all analyses were successful, False otherwise
    """
    sql_query = """
        SELECT patient_note_id
        FROM patient_notes
        WHERE patient_note_id NOT IN (
            SELECT patient_note_id FROM patient_documents
        );
    """

    all_visit_notes = get_select_query_result_dicts(sql_query)
    for a_visit_note_id in all_visit_notes:
        result = analyze_visit_note(a_visit_note_id["patient_note_id"])
        if not result:
            return False
    return True


def get_patient_record(patient_id: str) -> list[dict[str, Any]]:
    """Get all notes, documents, and billing information for a patient.

    Args:
        patient_id: Patient identifier

    Returns:
        List of patient records
    """
    sql_query = """
        SELECT
            pn.patient_id,
            pn.patient_note_id,
            pn.patient_note AS patient_note,
            pd.patient_document_id,
            pd.analysis_document AS patient_document,
            pc.codes_document AS patient_codes
        FROM
            patient_notes pn
        LEFT JOIN patient_documents pd ON
            pn.patient_id = pd.patient_id
            AND pn.patient_note_id = pd.patient_note_id
        LEFT JOIN patient_codes pc ON
            pd.patient_id = pc.patient_id
            AND pd.patient_document_id = pc.patient_document_id
        WHERE
            pd.patient_document_id IS NOT NULL
            AND pn.patient_id = %s;
    """

    patient_record = get_select_query_result_dicts(sql_query, (patient_id,))
    return patient_record
