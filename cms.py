#!/usr/bin/env python3
"""Collect Fee Schedules for CPT/HCPCS codes
"""

import hashlib
import requests
import json

from utils import ts_int_to_dt_obj
from utils import serialize_datetime
from database import insert_data_into_table

with open('2024_DHS_Code_List_Addendum_03_01_2024.txt') as afile:
    CODES = [line.rstrip('\n') for line in afile]

def get_details(hcpcs_code):
    """Get CPT code details and fee schedules, store as JSONB in
        PostgreSQL database
    """

    headers_options = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Access-Control-Request-Headers': 'content-type',
        'Access-Control-Request-Method': 'POST',
        'Connection': 'keep-alive',
        'Origin': 'https://www.cms.gov',
        'Referer': 'https://www.cms.gov/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }

    headers_post = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': 'https://www.cms.gov',
        'Referer': 'https://www.cms.gov/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"'
    }

    data_post = {
    "resources": [
        {
        "id": "da979697-996c-53ce-ae77-c58672a13443",
        "alias": "t"
        }
    ],
    "properties": [
        {
        "resource": "t",
        "property": "hcpc"
        },
        {
        "resource": "t",
        "property": "proc_stat"
        }
    ],
    "conditions": [
        {
        "resource": "t",
        "property": "hcpc",
        "value": f"{a_code}",
        "operator": "="
        }
    ],
    "sorts": [],
    "offset": 0,
    "limit": 500,
    "keys": True
    }

    data_all = {
    "resources": [
        {
        "id": "da979697-996c-53ce-ae77-c58672a13443",
        "alias": "i"
        },
        {
        "id": "d8882114-096f-59bb-b244-1ffb4848e497",
        "alias": "l"
        }
    ],
    "properties": [
        {
        "resource": "i",
        "property": "hcpc"
        },
        {
        "resource": "i",
        "property": "modifier"
        },
        {
        "resource": "i",
        "property": "proc_stat"
        },
        {
        "resource": "i",
        "property": "pctc"
        },
        {
        "resource": "i",
        "property": "nused_for_med"
        },
        {
        "resource": "i",
        "property": "rvu_work"
        },
        {
        "resource": "i",
        "property": "trans_nfac_pe_naflag"
        },
        {
        "resource": "i",
        "property": "trans_nfac_pe"
        },
        {
        "resource": "i",
        "property": "full_nfac_pe_naflag"
        },
        {
        "resource": "i",
        "property": "full_nfac_pe"
        },
        {
        "resource": "i",
        "property": "trans_fac_pe_naflag"
        },
        {
        "resource": "i",
        "property": "trans_fac_pe"
        },
        {
        "resource": "i",
        "property": "full_fac_pe_naflag"
        },
        {
        "resource": "i",
        "property": "full_fac_pe"
        },
        {
        "resource": "i",
        "property": "rvu_mp"
        },
        {
        "resource": "i",
        "property": "opps_nfac_pe"
        },
        {
        "resource": "i",
        "property": "opps_fac_pe"
        },
        {
        "resource": "i",
        "property": "opps_mp"
        },
        {
        "resource": "i",
        "property": "global"
        },
        {
        "resource": "i",
        "property": "mult_surg"
        },
        {
        "resource": "i",
        "property": "bilt_surg"
        },
        {
        "resource": "i",
        "property": "asst_surg"
        },
        {
        "resource": "i",
        "property": "co_surg"
        },
        {
        "resource": "i",
        "property": "team_surg"
        },
        {
        "resource": "i",
        "property": "phy_superv"
        },
        {
        "resource": "i",
        "property": "family_ind"
        },
        {
        "resource": "i",
        "property": "sdesc"
        },
        {
        "resource": "i",
        "property": "conv_fact"
        },
        {
        "resource": "i",
        "property": "nfac_pe_naflag"
        },
        {
        "resource": "i",
        "property": "fac_pe_naflag"
        },
        {
        "resource": "i",
        "property": "trans_nfac_total"
        },
        {
        "resource": "i",
        "property": "trans_fac_total"
        },
        {
        "resource": "i",
        "property": "full_nfac_total"
        },
        {
        "resource": "i",
        "property": "full_fac_total"
        },
        {
        "resource": "i",
        "property": "pre_op"
        },
        {
        "resource": "i",
        "property": "intra_op"
        },
        {
        "resource": "i",
        "property": "post_op"
        },
        {
        "resource": "i",
        "property": "endobase"
        },
        {
        "resource": "i",
        "property": "nfac_pe"
        },
        {
        "resource": "i",
        "property": "fac_pe"
        },
        {
        "resource": "i",
        "property": "nfac_total"
        },
        {
        "resource": "i",
        "property": "fac_total"
        },
        {
        "resource": "l",
        "property": "locality"
        },
        {
        "resource": "l",
        "property": "mac"
        },
        {
        "resource": "l",
        "property": "gpci_work"
        },
        {
        "resource": "l",
        "property": "gpci_pe"
        },
        {
        "resource": "l",
        "property": "gpci_mp"
        },
        {
        "alias": "nfac_price",
        "expression": {
            "operator": "*",
            "operands": [
            {
                "expression": {
                "operator": "+",
                "operands": [
                    {
                    "expression": {
                        "operator": "*",
                        "operands": [
                        {
                            "expression": {
                            "operator": "*",
                            "operands": [
                                {
                                "resource": "i",
                                "property": "rvu_work"
                                },
                                {
                                "resource": "i",
                                "property": "work_adjustor"
                                }
                            ]
                            }
                        },
                        {
                            "resource": "l",
                            "property": "gpci_work"
                        }
                        ]
                    }
                    },
                    {
                    "expression": {
                        "operator": "*",
                        "operands": [
                        {
                            "resource": "i",
                            "property": "trans_nfac_pe"
                        },
                        {
                            "resource": "l",
                            "property": "gpci_pe"
                        }
                        ]
                    }
                    },
                    {
                    "expression": {
                        "operator": "*",
                        "operands": [
                        {
                            "resource": "i",
                            "property": "rvu_mp"
                        },
                        {
                            "resource": "l",
                            "property": "gpci_mp"
                        }
                        ]
                    }
                    }
                ]
                }
            },
            {
                "resource": "i",
                "property": "conv_fact"
            }
            ]
        }
        },
        {
        "alias": "fac_price",
        "expression": {
            "operator": "*",
            "operands": [
            {
                "expression": {
                "operator": "+",
                "operands": [
                    {
                    "expression": {
                        "operator": "*",
                        "operands": [
                        {
                            "expression": {
                            "operator": "*",
                            "operands": [
                                {
                                "resource": "i",
                                "property": "rvu_work"
                                },
                                {
                                "resource": "i",
                                "property": "work_adjustor"
                                }
                            ]
                            }
                        },
                        {
                            "resource": "l",
                            "property": "gpci_work"
                        }
                        ]
                    }
                    },
                    {
                    "expression": {
                        "operator": "*",
                        "operands": [
                        {
                            "resource": "i",
                            "property": "trans_fac_pe"
                        },
                        {
                            "resource": "l",
                            "property": "gpci_pe"
                        }
                        ]
                    }
                    },
                    {
                    "expression": {
                        "operator": "*",
                        "operands": [
                        {
                            "resource": "i",
                            "property": "rvu_mp"
                        },
                        {
                            "resource": "l",
                            "property": "gpci_mp"
                        }
                        ]
                    }
                    }
                ]
                }
            },
            {
                "resource": "i",
                "property": "conv_fact"
            }
            ]
        }
        },
        {
        "alias": "nfac_limiting_charge",
        "expression": {
            "operator": "*",
            "operands": [
            {
                "expression": {
                "operator": "*",
                "operands": [
                    {
                    "expression": {
                        "operator": "+",
                        "operands": [
                        {
                            "expression": {
                            "operator": "*",
                            "operands": [
                                {
                                "expression": {
                                    "operator": "*",
                                    "operands": [
                                    {
                                        "resource": "i",
                                        "property": "rvu_work"
                                    },
                                    {
                                        "resource": "i",
                                        "property": "work_adjustor"
                                    }
                                    ]
                                }
                                },
                                {
                                "resource": "l",
                                "property": "gpci_work"
                                }
                            ]
                            }
                        },
                        {
                            "expression": {
                            "operator": "*",
                            "operands": [
                                {
                                "resource": "i",
                                "property": "trans_nfac_pe"
                                },
                                {
                                "resource": "l",
                                "property": "gpci_pe"
                                }
                            ]
                            }
                        },
                        {
                            "expression": {
                            "operator": "*",
                            "operands": [
                                {
                                "resource": "i",
                                "property": "rvu_mp"
                                },
                                {
                                "resource": "l",
                                "property": "gpci_mp"
                                }
                            ]
                            }
                        }
                        ]
                    }
                    },
                    {
                    "resource": "i",
                    "property": "conv_fact"
                    }
                ]
                }
            },
            1.0925
            ]
        }
        },
        {
        "alias": "fac_limiting_charge",
        "expression": {
            "operator": "*",
            "operands": [
            {
                "expression": {
                "operator": "*",
                "operands": [
                    {
                    "expression": {
                        "operator": "+",
                        "operands": [
                        {
                            "expression": {
                            "operator": "*",
                            "operands": [
                                {
                                "expression": {
                                    "operator": "*",
                                    "operands": [
                                    {
                                        "resource": "i",
                                        "property": "rvu_work"
                                    },
                                    {
                                        "resource": "i",
                                        "property": "work_adjustor"
                                    }
                                    ]
                                }
                                },
                                {
                                "resource": "l",
                                "property": "gpci_work"
                                }
                            ]
                            }
                        },
                        {
                            "expression": {
                            "operator": "*",
                            "operands": [
                                {
                                "resource": "i",
                                "property": "trans_fac_pe"
                                },
                                {
                                "resource": "l",
                                "property": "gpci_pe"
                                }
                            ]
                            }
                        },
                        {
                            "expression": {
                            "operator": "*",
                            "operands": [
                                {
                                "resource": "i",
                                "property": "rvu_mp"
                                },
                                {
                                "resource": "l",
                                "property": "gpci_mp"
                                }
                            ]
                            }
                        }
                        ]
                    }
                    },
                    {
                    "resource": "i",
                    "property": "conv_fact"
                    }
                ]
                }
            },
            1.0925
            ]
        }
        },
        {
        "alias": "opps_nfac_pmt_amt",
        "expression": {
            "operator": "*",
            "operands": [
            {
                "expression": {
                "operator": "+",
                "operands": [
                    {
                    "expression": {
                        "operator": "*",
                        "operands": [
                        {
                            "expression": {
                            "operator": "*",
                            "operands": [
                                {
                                "resource": "i",
                                "property": "rvu_work"
                                },
                                {
                                "resource": "i",
                                "property": "work_adjustor"
                                }
                            ]
                            }
                        },
                        {
                            "resource": "l",
                            "property": "gpci_work"
                        }
                        ]
                    }
                    },
                    {
                    "expression": {
                        "operator": "*",
                        "operands": [
                        {
                            "resource": "i",
                            "property": "opps_nfac_pe"
                        },
                        {
                            "resource": "l",
                            "property": "gpci_pe"
                        }
                        ]
                    }
                    },
                    {
                    "expression": {
                        "operator": "*",
                        "operands": [
                        {
                            "resource": "i",
                            "property": "opps_mp"
                        },
                        {
                            "resource": "l",
                            "property": "gpci_mp"
                        }
                        ]
                    }
                    }
                ]
                }
            },
            {
                "resource": "i",
                "property": "conv_fact"
            }
            ]
        }
        },
        {
        "alias": "opps_fac_pmt_amt",
        "expression": {
            "operator": "*",
            "operands": [
            {
                "expression": {
                "operator": "+",
                "operands": [
                    {
                    "expression": {
                        "operator": "*",
                        "operands": [
                        {
                            "expression": {
                            "operator": "*",
                            "operands": [
                                {
                                "resource": "i",
                                "property": "rvu_work"
                                },
                                {
                                "resource": "i",
                                "property": "work_adjustor"
                                }
                            ]
                            }
                        },
                        {
                            "resource": "l",
                            "property": "gpci_work"
                        }
                        ]
                    }
                    },
                    {
                    "expression": {
                        "operator": "*",
                        "operands": [
                        {
                            "resource": "i",
                            "property": "opps_fac_pe"
                        },
                        {
                            "resource": "l",
                            "property": "gpci_pe"
                        }
                        ]
                    }
                    },
                    {
                    "expression": {
                        "operator": "*",
                        "operands": [
                        {
                            "resource": "i",
                            "property": "opps_mp"
                        },
                        {
                            "resource": "l",
                            "property": "gpci_mp"
                        }
                        ]
                    }
                    }
                ]
                }
            },
            {
                "resource": "i",
                "property": "conv_fact"
            }
            ]
        }
        }
    ],
    "conditions": [
        {
        "resource": "i",
        "property": "hcpc",
        "value": f"{a_code}",
        "operator": "="
        }
    ],
    "joins": [
        {
        "resource": "l",
        "condition": {
            "resource": "i",
            "property": "year",
            "operator": "=",
            "value": {
            "resource": "l",
            "property": "year"
            }
        }
        }
    ],
    "offset": 0,
    "limit": 200,
    "sorts": [
        {
        "property": "hcpc",
        "order": "asc"
        },
        {
        "property": "locality",
        "order": "asc"
        },
        {
        "property": "proc_stat",
        "order": "asc"
        },
        {
        "property": "modifier",
        "order": "asc"
        }
    ],
    "keys": True
    }

    url1 = f'https://pfs.data.cms.gov/api/1/datastore/query?search=hcpcsCheck{a_code}&redirect=false&ACA='
    url2 = f'https://pfs.data.cms.gov/api/1/datastore/query?search=pricing_single_{a_code}&redirect=false&ACA='

    session = requests.Session()
    session.options(url1, headers=headers_options)
    session.post(url1, headers=headers_post, json=data_post)
    session.options(url2, headers=headers_options)
    session_response = session.post(url2, headers=headers_post, json=data_all)

    results = json.loads(json.dumps(session_response.json()))['results']
    return results

ts = serialize_datetime(ts_int_to_dt_obj())
for a_code in CODES:
    datas = get_details(a_code)
    if datas:
        for a_data in datas:
            data_sha256 = hashlib.sha256(json.dumps(a_data, sort_keys=True).encode('utf-8')).hexdigest()
            codes_data = {
                          'timestamp' : ts,
                          'sha256' : data_sha256,
                          'codes_document' : json.dumps(a_data)
                         }
            insert_data_into_table('cpt_hcpcs_codes', codes_data)
    else:
        print(a_code, "has no data available")
