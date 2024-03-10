#!/usr/bin/env python3

import re
import simple_icd_10_cm as icddetails
import icd10 as icdbilling

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
