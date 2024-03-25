#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup

def lookup_cpt_codes(cpt_code_list):
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


            cpt = {
                'cpt': cpt,
                'details' : cptdesc
                }
            return cpt
        except AttributeError as e:
            print (f'{cpt_code} not found')

cpt_codes = ['43850', '90865', '74230']
lookup_cpt_codes(cpt_codes)
