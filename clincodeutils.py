#!/usr/bin/env python3

import asyncio
import json
import logging
import re
import requests
from gptutils import prompt_chat
import simple_icd_10_cm as icddetails
import icd10 as icdbilling
from bs4 import BeautifulSoup

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

def icd_10_code_details(icd_10_code):
    """ICD-10 code details
    """

    try:
        full_details =  icddetails.get_full_data(icd_10_code)
        icd_details_obj = {
                            'code' : icd_10_code,
                            'full_data' : full_details.replace(':\n',':'),
                            'billable' : icdbilling.find(icd_10_code).billable
                          }

        return icd_details_obj
    except ValueError as e:
        return e.args[0]

def icd_10_code_details_list(list_of_icd_10_codes):
    """Details about each icd-10 code found
    """
    
    details_list = []

    for icd_10_code in list_of_icd_10_codes:
        details = icd_10_code_details(icd_10_code)
        details_list.append(details)

    return details_list

def lookup_cpt_gpt(cpt_code_list):
    """Lookup cpt codes using llama2
    """

    cpt_details = []
    for cpt_code in cpt_code_list:
        code_lookup_prompt = f"""Explain CPT code {cpt_code}. Respond with JSON only. Keys cpt is the code number, \
        details is a dictionary with nested keys short_description and long_description. JSON template {{"cpt": "actual \
        cpt code", "details": {{"short_description": "short description goes here", "long_description": "long \
        description goes here"}}}}"""

        result = asyncio.run(prompt_chat('llama2', code_lookup_prompt + '', False))
        cpt_details.append(result['analysis'])

    return cpt_details
