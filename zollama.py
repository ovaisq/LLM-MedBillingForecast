#!/usr/bin/env python3
"""Reddit Data Scrapper Service
    ©2024, Ovais Quraishi

    Collects submissions, comments for each submission, author of each submission,
    author of each comment to each submission, and all comments for each author.
    Also, subscribes to subreddit that a submission was posted to

    Uses Gunicorn WSGI

    Install Python Modules:
        > pip3 install -r requirements.txt

    Get Reddit API key: https://www.reddit.com/wiki/api/

    Gen SSL key/cert
        > openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 3650

    Create Database and tables:
        zollama.sql

    Generate Flask App Secret Key:
        >  python -c 'import secrets; print(secrets.token_hex())'

    Update setup.config with pertinent information (see setup.config.template)

    Run Service:
    (see https://docs.gunicorn.org/en/stable/settings.html for config details)

        > gunicorn --certfile=cert.pem \
                   --keyfile=key.pem \
                   --bind 0.0.0.0:5000 \
                   zollama:app \
                   --timeout 2592000 \
                   --threads 4 \
                   --reload

    Customize it to your hearts content!

    LICENSE: The 3-Clause BSD License - license.txt

    TODO:
        - Add Swagger Docs
        - Add long running task queue
            - Queue: task_id, task_status, end_point
            - Kafka
        - Revisit Endpoint logic add robust error handling
        - Add scheduler app - to schedule some of these events
            - scheduler checks whether or not a similar tasks exists
        - Add logic to handle list of lists with NUM_ELEMENTS_CHUNK elementsimport configparser
"""

import asyncio
import json
import logging
from flask import Flask, request, jsonify, abort
from flask_jwt_extended import JWTManager, jwt_required, create_access_token

# Import required local modules
from config import get_config
from clincodeutils import extract_icd10_codes
from clincodeutils import extract_cpt_codes
from clincodeutils import icd_10_code_details_list
from clincodeutils import lookup_cpt_gpt
from database import insert_data_into_table
from database import get_select_query_result_dicts
from encryption import decrypt_text
from gptutils import prompt_chat
from utils import ts_int_to_dt_obj
from utils import serialize_datetime

app = Flask('ZOllama-GPT')

# constants
CONFIG = get_config()

NUM_ELEMENTS_CHUNK = 25
LLMS = CONFIG.get('service','LLMS').split(',')
MEDLLMS = CONFIG.get('service','MEDLLMS').split(',')

# Flask app config
app.config.update(
                  JWT_SECRET_KEY=CONFIG.get('service', 'JWT_SECRET_KEY'),
                  SECRET_KEY=CONFIG.get('service', 'APP_SECRET_KEY'),
                  PERMANENT_SESSION_LIFETIME=172800 #2 days
                 )
jwt = JWTManager(app)

@app.route('/login', methods=['POST'])
def login():
    """Generate JWT
    """

    secret = request.json.get('api_key')

    if secret != CONFIG.get('service','SRVC_SHARED_SECRET'):  # if the secret matches
        return jsonify({"message": "Invalid secret"}), 401

    # generate access token
    access_token = create_access_token(identity=CONFIG.get('service','IDENTITY'))
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
                        patient_notes;
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

    sql_query = f"""SELECT
                        patient_id, patient_note_id, patient_note
                   FROM
                        patient_notes
                   WHERE patient_note_id = '{visit_note_id}';
                """

    visit_notes = get_select_query_result_dicts(sql_query)

    for visit_note in visit_notes:
        patient_id = visit_note['patient_id']
        patient_note_id = visit_note['patient_note_id']

        # decrypt patient note content
        content = decrypt_text(visit_note['patient_note']['note'])

        prompt = "What Disease does this Patient Have? P is patient, D is Doctor"
        summarized_obj = asyncio.run(prompt_chat('deepseek-llm', prompt + content))

        if summarized_obj:
            recommended_diagnosis = decrypt_text(summarized_obj['analysis'])

            # process diagnosis for ICD/CPT codes
            for llm in MEDLLMS:
                analyzed_obj = asyncio.run(
                                           prompt_chat(
                                                       llm,
                                                       'Diagnose this patient: ' +
                                                       recommended_diagnosis
                                                      )
                                          )

                # decrypt analysis result for ICD/CPT processing only
                decrypted_analysis = decrypt_text(analyzed_obj['analysis'])
                get_store_icd_cpt_codes(
                                        patient_id,
                                        analyzed_obj['shasum_512'],
                                        llm,
                                        decrypted_analysis
                                       )

                if not encrypt_analysis:
                    logging.error('URGENT: Patient Data Encryption disabled! \
                                If spotted in Production logs, notify immediately!')

                # construct patient data object for storage
                patient_data_obj = {
									'schema_version': '3',
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
										 'patient_id': patient_id,
										 'patient_note_id': patient_note_id,
										 'analysis_document': json.dumps(patient_data_obj)
									    }

                insert_data_into_table('patient_documents', patient_analysis_data)
                return True
        else:
            return False

def get_store_icd_cpt_codes(patient_id, patient_document_id, llm, analyzed_content):
    """Get icd and cpt codes for the diagnosis and store the two
        as JSON in the table
    """

    prompts = {
               'icd': 'What are the ICD codes for this diagnosis? ',
               'cpt': 'What are the CPT codes for this diagnosis? ',
               'prescription': 'What medication to prescribe for the diagnosis? ',
               'prescription_cpt': 'What are the CPT codes for these prescriptions? '
              }

    # adjust prompts if llm is 'meditron'
    if llm == 'meditron':
        prompts['prescription_cpt'] = prompts['prescription']

    # do not encrypt
    icd_obj = asyncio.run(prompt_chat(llm, prompts['icd'] + analyzed_content, False))

    # do not encrypt
    cpt_obj = asyncio.run(prompt_chat(llm, prompts['cpt'] + analyzed_content, False))

    # do not encrypt
    prescription_obj = asyncio.run(
                                   prompt_chat(
                                               llm,
                                               prompts['prescription'] + analyzed_content,
                                               False
                                              )
                                  )
    prescription_analysis = prescription_obj['analysis']

    # do not encrypt
    prescription_cpt_obj = asyncio.run(
                                       prompt_chat(
                                                   llm,
                                                   prompts['prescription_cpt'] +
                                                   prescription_analysis,
                                                   False
                                                  )
                                      )

    icd_10_code_details = icd_10_code_details_list(extract_icd10_codes(icd_obj['analysis']))
    prescription_cpt_details = lookup_cpt_gpt(extract_cpt_codes(prescription_cpt_obj['analysis']))

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
        'prescription': {
            'timestamp': serialize_datetime(prescription_obj['timestamp']),
            'prescriptions': prescription_obj['analysis']
        },
        'prescription_cpt': {
            'timestamp': serialize_datetime(prescription_cpt_obj['timestamp']),
            'codes': extract_cpt_codes(prescription_cpt_obj['analysis']),
            'details': prescription_cpt_details
        }
    }

    codes_data = {
        'timestamp': serialize_datetime(ts_int_to_dt_obj()),
        'patient_id': patient_id,
        'patient_document_id': patient_document_id,
        'codes_document': json.dumps(codes_document)
    }

    insert_data_into_table('patient_codes', codes_data)

def get_patient_record(patient_id):
    """Get all notes, documents, and billing information available
        for a given patient_id
    """

    sql_query = f"""
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
                        AND pn.patient_id = '{patient_id}';
                 """

    patient_record = get_select_query_result_dicts(sql_query)

    return patient_record

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO) # init logging
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    # non-production WSGI settings:
    #  port 5000, listen to local ip address, use ssl
    # in production we use gunicorn
    app.run(port=5000,
            host='0.0.0.0',
            ssl_context=('cert.pem', 'key.pem'),
            debug=False) # not for production
