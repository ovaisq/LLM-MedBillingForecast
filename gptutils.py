#!/usr/bin/env python3
"""Ollama-GPT module
    ©2024, Ovais Quraishi
"""

import hashlib
import logging
import httpx
import sys

from ollama import Client

from config import get_config
from encryption import encrypt_text
from utils import ts_int_to_dt_obj
from utils import sanitize_string
from utils import check_endpoint_health

CONFIG = get_config()

def prompt_chat(llm,
                      content,
                      encrypt_analysis=CONFIG.getboolean('service',
                                                         'PATIENT_DATA_ENCRYPTION_ENABLED')
                     ):
    """Llama Chat Prompting and response
    """

    ollama_server = CONFIG.get('service','OLLAMA_API_URL')

    if not check_endpoint_health(ollama_server):
       logging.error('Ollama Server %s is not available', ollama_server)
       return False

    dt = ts_int_to_dt_obj()
    client = Client(host=ollama_server)
    logging.info('Running for %s', llm)
    try:
        response = client.chat(
                                        model=llm,
                                        stream=False,
                                        messages=[
                                                  {
                                                   'role': 'user',
                                                   'content': content
                                                  },
                                                 ],
                                        options = {
                                                    'temperature' : 0
                                                  }
                                    )

        # chatgpt analysis
        analysis = response['message']['content']
        analysis = sanitize_string(analysis)

        # this is for the analysis text only - the idea is to avoid
        #  duplicate text document, to allow indexing the column so
        #  to speed up search/lookups
        analysis_sha512 = hashlib.sha512(str.encode(analysis)).hexdigest()

        # see encryption.py module
        # encrypt text *** make sure that encryption key file is secure! ***

        if encrypt_analysis:
            analysis = encrypt_text(analysis).decode('utf-8')

        analyzed_obj = {
                        'timestamp' : dt,
                        'shasum_512' : analysis_sha512,
                        'analysis' : analysis
                        }

        return analyzed_obj
    except (httpx.ReadError, httpx.ConnectError, httpx.RemoteProtocolError) as e:
        logging.error('Error: %s', e.args[0])
        logging.error('Unable to reach Ollama Server: %s', CONFIG.get('service','OLLAMA_API_URL'))
        return False
