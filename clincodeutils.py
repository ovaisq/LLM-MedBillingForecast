#!/usr/bin/env python3
""" ©2024, Ovais Quraishi """

import ast

import logging
import re
from gptutils import prompt_chat

def extract_icd10_codes(text):
    """Extract ICD-10 codes from a string.
    """

    lookup_pattern = r'\b[A-TV-Z]\d{2}(?:\.\d{1,3})?\b'
    return re.findall(lookup_pattern, text)

def extract_cpt_codes(text):
    """Extract CPT codes from a string
    """

    lookup_pattern = r'\b\d{5}\b'
    return re.findall(lookup_pattern, text)

def extract_hcpcs_codes(text):
    """Extract hcpcs codes from a string
    """

    lookup_pattern = r'\b\d{5}\b'
    return re.findall(lookup_pattern, text)

def icd_10_code_details(icd_10_code):
    """ICD-10 code details
    """

    try:
        icd_details_obj = lookup_icd_gpt(icd_10_code)
        return icd_details_obj['analysis']
    except (ValueError, AttributeError) as e:
        logging.error('Error: %s, %s', icd_10_code, e.args[0])
        return e.args[0]

def icd_10_code_details_list(list_of_icd_10_codes):
    """Details about each icd-10 code found
    """

    details_list = []

    for icd_10_code in list_of_icd_10_codes:
        # should be dictionary object
        detail = icd_10_code_details(icd_10_code).replace('  ','').replace('\n','')
        details = ast.literal_eval(detail)
        details_list.append(details)

    return details_list

def lookup_icd_gpt(icd_code):
    """Lookup icd codes using llama3.2
    """

    code_lookup_prompt = f"""Response MUST BE JSON ONLY, no additional comments. Tell me about ICD-10 code {icd_code}, is it billable? Respond in JSON only. Use the following python JSON template, \
    the JSON needs to be python compliant where boolean "true" needs to be represented as True and \
    "false" as False: \
     {{'code': 'icd-10 code goes here',
        'billable': BOOLEAN,
        'full_data': {{
            'short_description': 'short description goes here',
            'long_description': 'long description goes here',
            'billing_guidelines': {{
                'insurance_company': {{
                    'reimbursement_rate': 'REIMBURSEMENT RATE from the insurance company goes here',
                    'billing_instructions': 'billing instructions from the insurance company go here'
                }},
                'medical_provider': {{
                    'reimbursement_rate': 'REIMBURSEMENT RATE from the medical provider goes here',
                    'billing_instructions': 'billing instructions from the medical provider go here'
                }}
            }}
        }}}}
    """

    icd_details = prompt_chat('llama3.2', code_lookup_prompt + '', False)

    return icd_details

def lookup_cpt_gpt(cpt_code_list):
    """Lookup cpt codes using llama3.2
    """

    cpt_details = []
    for cpt_code in cpt_code_list:
        code_lookup_prompt = f"""Explain CPT code {cpt_code}. Respond with JSON only. Keys cpt is the code number, \
        details is a dictionary with nested keys short_description and long_description. JSON template {{"cpt": "actual \
        cpt code", "details": {{"short_description": "short description goes here", "long_description": "long \
        description goes here"}}}}"""

        result = prompt_chat('llama3.2', code_lookup_prompt + '', False)
        cpt_details.append(result['analysis'])

    return cpt_details

def lookup_hcpcs_gpt(hcpcs_code_list):
    """Lookup hcpcs codes using llama3.2
    """

    hcpcs_details = []
    for hcpcs_code in hcpcs_code_list:
        code_lookup_prompt = f"""Explain HCPCS code {hcpcs_code}. Respond with JSON only. Keys cpt is the code number, \
        details is a dictionary with nested keys short_description and long_description. JSON template {{"hcpcs": "actual \
        hcpcs code", "details": {{"short_description": "short description goes here", "long_description": "long \
        description goes here"}}}}"""

        result = prompt_chat('llama3.2', code_lookup_prompt + '', False)
        hcpcs_details.append(result['analysis'])

    return hcpcs_details
