#!/usr/bin/env python3
"""Agentic-AI based Medical Billing Forecaster"""

import asyncio
import os
import json
import logging
from flask import Flask, request, jsonify, abort
from flask_jwt_extended import JWTManager, jwt_required, create_access_token

# Import required local modules
from config import get_config
from clincodeutils import extract_icd10_codes
from clincodeutils import extract_cpt_codes
from clincodeutils import extract_hcpcs_codes
from clincodeutils import icd_10_code_details_list
from clincodeutils import lookup_cpt_gpt
from clincodeutils import lookup_hcpcs_gpt
from database import insert_data_into_table
from database import get_select_query_result_dicts
from encryption import decrypt_text
from gptutils import prompt_chat
from utils import ts_int_to_dt_obj
from utils import serialize_datetime

app = Flask('BillingForecast-GPT')

# constants
CONFIG = get_config()

NUM_ELEMENTS_CHUNK = 25
LLMS = os.environ['LLMS'].split(',')
MEDLLMS = os.environ['MEDLLMS'].split(',')

# Flask app config
app.config.update(
                  JWT_SECRET_KEY=os.environ['JWT_SECRET_KEY'],
                  SECRET_KEY=os.environ['APP_SECRET_KEY'],
                  PERMANENT_SESSION_LIFETIME=172800 #2 days
                 )
jwt = JWTManager(app)

@app.route('/login', methods=['POST'])
def login():
    """Generate JWT
    """

    secret = request.json.get('api_key')

    if secret != os.environ['SRVC_SHARED_SECRET']:  # if the secret matches
        return jsonify({"message": "Invalid secret"}), 401

    # generate access token
    access_token = create_access_token(identity=os.environ['IDENTITY'])
    return jsonify(access_token=access_token), 200

@app.route('/analyze_visit_notes', methods=['GET'])
@jwt_required()
def analyze_visit_notes_endpoint():
    """Analyze all OSCE format Visit Notes that exist in database
    """

    if not analyze_visit_notes():
        abort(502, description="Ollama Server not available")
    return jsonify({'message': 'analyze_visit_notes endpoint'})

@app.route('/analyze_visit_note', methods=['GET'])
@jwt_required()
def analyze_visit_note_endpoint():
    """Analyze OSCE format Visit Note that exists in the database
    """

    visit_note_id = request.args.get('visit_note_id')
    analyze_visit_note(visit_note_id)
    return jsonify({'message': 'analyze_visit_note endpoint'})

@app.route('/get_patient', methods=['GET'])
@jwt_required()
def get_patient_endpoint():
    """Get a patient record
    """

    patient_id = request.args.get('patient_id')
    get_patient_record(patient_id)
    return jsonify({'message': 'get_patient endpoint'})

def analyze_visit_notes():
    """Analyze all visit notes in the db
    """

    sql_query = """SELECT
                        patient_note_id
                   FROM 
                        patient_notes
                   WHERE patient_note_id NOT IN (SELECT patient_note_id FROM patient_documents);
                """

    all_visit_notes = get_select_query_result_dicts(sql_query)
    for a_visit_note_id in all_visit_notes:
        result = analyze_visit_note(a_visit_note_id['patient_note_id'])
        if not result:
            return False
    return True

def analyze_visit_note(visit_note_id):
    """Analyze a specific visit note that exists in the database
    """

    encrypt_analysis = CONFIG.getboolean('service', 'PATIENT_DATA_ENCRYPTION_ENABLED')

    sql_query = """SELECT
                        patient_id, patient_note_id, patient_note, patient_note ->> 'locality' as patient_locality
                   FROM
                        patient_notes
                   WHERE patient_note_id = %s;
                """

    visit_notes = get_select_query_result_dicts(sql_query, (visit_note_id,))

    for visit_note in visit_notes:
        logging.info(visit_note['patient_note_id'][0:10])
        patient_id = visit_note['patient_id']
        patient_note_id = visit_note['patient_note_id']

        # decrypt patient note content
        content = decrypt_text(visit_note['patient_note']['note'])

        prompt = "What disease does this patient have? P is patient, D is Doctor"
        summarized_obj = prompt_chat('phi4', prompt + content)

        if summarized_obj:
            recommended_diagnosis = decrypt_text(summarized_obj['analysis'])

            # process diagnosis for ICD/CPT codes
            for llm in MEDLLMS:
                analyzed_obj =             prompt_chat(
                                                       llm,
                                                       'Diagnose this patient: ' +
                                                       recommended_diagnosis
                                                      )
                                          

                # decrypt analysis result for ICD/CPT processing only
                decrypted_analysis = decrypt_text(analyzed_obj['analysis'])
                asyncio.run(get_store_icd_cpt_codes(
                                        patient_id,
                                        analyzed_obj['shasum_512'],
                                        llm,
                                        decrypted_analysis
                                       ))

                if not encrypt_analysis:
                    app.logger.error('URGENT: Patient Data Encryption disabled! \
                                If spotted in Production logs, notify immediately!')

                # construct patient data object for storage
                patient_data_obj = {
                                    'schema_version': '4',
                                    'llm': llm,
                                    'source': 'healthcare',
                                    'category': 'patient',
                                    'patient_id': patient_id,
                                    'patient_note_id': patient_note_id,
                                    'osce_note_summarized': summarized_obj['analysis'],
                                    'analysis_document': analyzed_obj['analysis']
                                   }

                patient_analysis_data = {
                                         'timestamp': analyzed_obj['timestamp'],
                                         'patient_document_id': analyzed_obj['shasum_512'],
                                          'patient_locality' : visit_note['patient_locality'],
                                         'patient_id': patient_id,
                                         'patient_note_id': patient_note_id,
                                         #json.loads this when read back from database
                                         'analysis_document': json.dumps(patient_data_obj)
                                        }

                insert_data_into_table('patient_documents', patient_analysis_data)
                return True
        else:
            return False

async def get_store_icd_cpt_codes(patient_id, patient_document_id, llm, analyzed_content):
    """Get ICD and CPT codes for the diagnosis and store them as JSON in the table."""
    
    prompts = {
        'icd': 'What are the ICD codes for this diagnosis? ',
        'cpt': 'What are the CPT codes for this diagnosis? ',
        'hcpcs': 'What are the HCPCS codes for this diagnosis? ',
        'prescription': 'What medication to prescribe for the diagnosis? ',
        'prescription_cpt': 'What are the CPT codes for these prescriptions? ',
        'prescription_hcpcs': 'What are the HCPCS codes for these prescriptions? '
    }

    # Adjust prompts if llm is 'meditron'
    if llm == 'meditron':
        prompts['prescription_cpt'] = prompts['prescription']

    async def fetch_code(prompt_key, content):
        return prompt_chat(llm, prompts[prompt_key] + content, False)

    # Gather all asynchronous tasks
    icd_obj, cpt_obj, hcpcs_obj, prescription_obj = await asyncio.gather(
        fetch_code('icd', analyzed_content),
        fetch_code('cpt', analyzed_content),
        fetch_code('hcpcs', analyzed_content),
        fetch_code('prescription', analyzed_content)
    )

    prescription_analysis = prescription_obj['analysis']

    # Further gather tasks for prescriptions
    prescription_cpt_obj, prescription_hcpcs_obj = await asyncio.gather(
        fetch_code('prescription_cpt', prescription_analysis),
        fetch_code('prescription_hcpcs', prescription_analysis)
    )

    icd_10_code_details = icd_10_code_details_list(extract_icd10_codes(icd_obj['analysis']))
    prescription_cpt_details = lookup_cpt_gpt(extract_cpt_codes(prescription_cpt_obj['analysis']))
    prescription_hcpcs_details = lookup_hcpcs_gpt(extract_hcpcs_codes(prescription_hcpcs_obj['analysis']))

    hcpcs_codes = extract_hcpcs_codes(hcpcs_obj['analysis'])

    codes_document = {
        'icd': {
            'timestamp': serialize_datetime(icd_obj['timestamp']),
            'codes': extract_icd10_codes(icd_obj['analysis']),
            'details': icd_10_code_details
        },
        'cpt': {
            'timestamp': serialize_datetime(cpt_obj['timestamp']),
            'codes': extract_cpt_codes(cpt_obj['analysis']),
            'details': lookup_cpt_gpt(extract_cpt_codes(cpt_obj['analysis']))
        },
        'hcpcs': {
            'timestamp': serialize_datetime(hcpcs_obj['timestamp']),
            'codes': hcpcs_codes,
            'details': lookup_hcpcs_gpt(hcpcs_codes)
        },
        'prescription': {
            'timestamp': serialize_datetime(prescription_obj['timestamp']),
            'prescriptions': prescription_obj['analysis']
        },
        'prescription_cpt': {
            'timestamp': serialize_datetime(prescription_cpt_obj['timestamp']),
            'codes': extract_cpt_codes(prescription_cpt_obj['analysis']),
            'details': prescription_cpt_details
        },
        'prescription_hcpcs': {
            'timestamp': serialize_datetime(prescription_hcpcs_obj['timestamp']),
            'codes': extract_hcpcs_codes(prescription_hcpcs_obj['analysis']),
            'details': prescription_hcpcs_details
        }
    }

    codes_data = {
        'timestamp': serialize_datetime(ts_int_to_dt_obj()),
        'patient_id': patient_id,
        'patient_document_id': patient_document_id,
        # json.loads this when read back from the database
        'codes_document': json.dumps(codes_document)
    }

    insert_data_into_table('patient_codes', codes_data)

def get_patient_record(patient_id):
    """Get all notes, documents, and billing information available
        for a given patient_id
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
                        and pn.patient_note_id = pd.patient_note_id
                    LEFT JOIN patient_codes pc ON
                        pd.patient_id = pc.patient_id
                        AND pd.patient_document_id = pc.patient_document_id
                    WHERE
                        pd.patient_document_id IS NOT NULL
                        AND pn.patient_id = %s;
                 """

    patient_record = get_select_query_result_dicts(sql_query, (patient_id,))

    return patient_record

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO) # init logging

    # non-production WSGI settings:
    #  port 5000, listen to local ip address, use ssl
    # in production we use gunicorn
    app.run(port=5009,
            host='0.0.0.0',
            ssl_context=('cert.pem', 'key.pem'),
            debug=False) # not for production
