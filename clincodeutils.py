#!/usr/bin/env python3

import re
import requests
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

def lookup_cpt_codes(cpt_code_list):
    """Unable to find a reliable free CPT lookup service - so using this
        hack for now.
    """

    cpt_details = []

    url = 'https://reports.nsqip.facs.org/CQILookupToolV2/lookupToolService'
    headers = {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Accept': '*/*',
                'Sec-Fetch-Site': 'same-origin',
                'Accept-Encoding': 'gzip, deflate, br',
                'Sec-Fetch-Mode': 'cors',
                'Host': 'reports.nsqip.facs.org',
                'Origin': 'https://reports.nsqip.facs.org',
                'Referer': 'https://reports.nsqip.facs.org/CQILookupToolV2/?ctx=adult',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Cookie': 'JSESSIONID=6168C17923E03E8178E68D113F9A22B3; ACS_SHARED_SESSION_ID=31b6d8f9-0d1d-46e9-b3a5-fdd14d01434f; JSESSIONID=2F71D4EB8D986AB83E5ADD3A2F8A8FB6'
               }


    for cpt_code in cpt_code_list:
        try:
            data = {
                    'keywords': cpt_code,
                    'year': '2024',
                    'incCodesAcceptedPrevYear': 'true',
                    'acceptedCodes': 'false',
                    'context': 'adult'
                   }

            response = requests.post(url, headers=headers, data=data)

            html = response.json()['result']

            soup = BeautifulSoup(html, 'html.parser')

            cpt = soup.find('td', class_='cpt').text
            cptdesc = soup.find('td', class_='cptdesc').text

            cpt_data = {
                        'cpt': cpt,
                        'details' : cptdesc.strip()
                       }

            cpt_details.append(cpt_data)

        except AttributeError as e:

            cpt_data = {
                        'cpt': cpt_code,
                        'details' : 'No data found'
                       }

            cpt_details.append(cpt_data)

    return cpt_details
