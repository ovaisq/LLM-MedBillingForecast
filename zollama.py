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
        reddit.sql

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
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token

# Import required local modules
from config import get_config
from clincodeutils import extract_icd10_codes
from clincodeutils import extract_cpt_codes
from clincodeutils import icd_10_code_details_list
from clincodeutils import lookup_cpt_codes
from database import insert_data_into_table
from database import get_select_query_result_dicts
from encryption import encrypt_text, decrypt_text
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

    analyze_visit_notes()
    return jsonify({'message': 'analyze_visit_notes endpoint'})

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
        analyze_visit_note(a_visit_note_id['patient_note_id'])

@app.route('/analyze_visit_note', methods=['GET'])
@jwt_required()
def analyze_visit_note_endpoint():
    """Analyze OSCE format Visit Note that exists in the database
    """

    visit_note_id = request.args.get('visit_note_id')
    analyze_visit_note(visit_note_id)
    return jsonify({'message': 'analyze_visit_note endpoint'})

def analyze_visit_note(visit_note_id):
    """Analyze a specific visit note that exists in the database
    """

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

        # this note text is encrypted in the patient_notes table
        content = decrypt_text(visit_note['patient_note']['note'])

        prompt = "What Disease does this Patient Have? P is patient, D is Doctor"
        summarized_obj, _ = asyncio.run(prompt_chat('deepseek-llm', prompt + content))

        # summary is created here, and then used for diagnostics, should be encrypted when
        #  before storing it in db
        osce_note_summarized = summarized_obj['analysis']
        prompt = 'Diagnose this patient: '

        # PII should always be encrypted
        for llm in MEDLLMS:
            analyzed_obj, encrypt_analysis = asyncio.run(
                                                         prompt_chat(
                                                                     llm,
                                                                     prompt +
                                                                     summarized_obj['analysis']
                                                                    )
                                                        )
            # decrypt for ICD/DPT codes processing only. this happens and should ONLY happen here
            recommended_diagnosis = decrypt_text(analyzed_obj['analysis'])
            patient_document_id = analyzed_obj['shasum_512']
            get_store_icd_cpt_codes(patient_id, patient_document_id, llm, recommended_diagnosis)
            recommended_diagnosis = analyzed_obj['analysis'] #originally encrypted

            if encrypt_analysis:
                osce_note_summarized = encrypt_text(summarized_obj['analysis']).decode('utf-8')
            else:
                logging.error('URGENT: Patient Data Encryption disabled! \
                              If spotted in Production logs, notify immediately!')

            patient_data_obj = {
                                'schema_version' : '3',
                                'llm' : llm,
                                'source' : 'healthcare',
                                'category' : 'patient',
                                'patient_id' : patient_id,
                                'patient_note_id' : patient_note_id,
                                'osce_note_summarized' : osce_note_summarized,
                                'analysis_document' : recommended_diagnosis 
                                }
            patient_analysis_data = {
                                        'timestamp' : analyzed_obj['timestamp'],
                                        'patient_document_id' : patient_document_id,
                                        'patient_id' : patient_id,
                                        'patient_note_id' : patient_note_id,
                                        'analysis_document' : json.dumps(patient_data_obj)
                                        }
            insert_data_into_table('patient_documents', patient_analysis_data)

def get_store_icd_cpt_codes(patient_id, patient_document_id, llm, analyzed_content):
    """Get icd and cpt codes for the diagnosis and store the two
        as JSON in the table
    """

    if llm != 'meditron':
        icd_prompt = 'What are the ICD codes for this diagnosis? '
        cpt_prompt = 'What are the CPT codes for this diagnosis? '
        prescription_prompt = 'What medication to prescribe for the diagnosis? '
        prescription_cpt_prompt = 'What are the CPT codes for these prescriptions? '

    if llm == 'meditron':
        icd_prompt = 'What are the ICD codes for this diagnosis? '
        cpt_prompt = 'What are the CPT codes for this diagnosis? '
        prescription_prompt = 'What medication to prescribe for the diagnosis? '

    # do not encrypt
    icd_obj, _ = asyncio.run(prompt_chat(llm, icd_prompt + analyzed_content, False))

    # do not encrypt
    cpt_obj, _ = asyncio.run(prompt_chat(llm, cpt_prompt + analyzed_content, False))

    # do not encrypt
    prescription_obj, _ = asyncio.run(prompt_chat(llm, prescription_prompt + analyzed_content, False))

    # do not encrypt
    prescription_cpt_obj, _ = asyncio.run(prompt_chat(llm, prescription_cpt_prompt + prescription_obj['analysis'], False))

    codes_document = {
                      'icd' : {
                               'timestamp' : serialize_datetime(icd_obj['timestamp']),
                               'codes' : extract_icd10_codes(icd_obj['analysis']),
                               'details' : icd_10_code_details_list(extract_icd10_codes(icd_obj['analysis']))
                              },
                      'cpt' : { 
                               'timestamp' : serialize_datetime(cpt_obj['timestamp']),
                               'codes' : extract_cpt_codes(cpt_obj['analysis']),
                               'details' : lookup_cpt_codes(extract_cpt_codes(cpt_obj['analysis']))
                              },
                      'prescription' : { 
                                         'timestamp' : serialize_datetime(prescription_obj['timestamp']),
                                         'prescriptions' : prescription_obj['analysis']
                                        },
                      'prescription_cpt' : {
                                            'timestamp' : serialize_datetime(prescription_cpt_obj['timestamp']),
                                            'codes' : extract_cpt_codes(prescription_cpt_obj['analysis']),
                                            'details' : lookup_cpt_codes(extract_cpt_codes(prescription_cpt_obj['analysis']))
                                           }
                     }
    codes_data = {
                  'timestamp' : serialize_datetime(ts_int_to_dt_obj()),
                  'patient_id' : patient_id,
                  'patient_document_id' : patient_document_id,
                  'codes_document' : json.dumps(codes_document)
                 }
    insert_data_into_table('patient_codes', codes_data)

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
