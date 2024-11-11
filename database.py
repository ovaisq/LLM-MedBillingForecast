# database.py
# ©2024, Ovais Quraishi

import psycopg2
import logging
from config import get_config

def psql_connection():
    """Connect to PostgreSQL server"""

    db_config = get_config()['psqldb']
    try:
        psql_conn = psycopg2.connect(**db_config)
        psql_cur = psql_conn.cursor()
        return psql_conn, psql_cur
    except psycopg2.Error as e:
        logging.error("Error connecting to PostgreSQL: %s", e)
        raise

def execute_query(sql_query):
    """Execute a SQL query"""

    conn, cur = psql_connection()
    try:
        cur.execute(sql_query)
        result = cur.fetchall()
        conn.close()
        return result
    except psycopg2.Error as e:
        logging.error("%s", e)
        raise

def insert_data_into_table(table_name, data):
    """Insert data into table"""

    conn, cur = psql_connection()
    try:
        placeholders = ', '.join(['%s'] * len(data))
        columns = ', '.join(data.keys())
        # Since the table keys that matter are set to UNIQUE value,
        #   I find the ON CONFLICT DO NOTHING more effecient than
        #   doing a lookup before INSERT. This way original content
        #   is preserved by default. In case of updating existing
        #   data, one can write a method to safely update data
        #   while also preserving original data. For example use
        #   ON CONFLICT DO UPDATE. For now this'd do.
        sql_query = f"""INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) \
                     ON CONFLICT DO NOTHING;"""
        cur.execute(sql_query, list(data.values()))
        conn.commit()
    except psycopg2.Error as e:
        logging.error("%s", e)
        raise

def get_select_query_results(sql_query):
    """Execute a query, return all rows for the query
    """

    conn, cur = psql_connection()
    try:
        cur.execute(sql_query)
        result = cur.fetchall()
        conn.close()
        return result
    except psycopg2.Error as e:
        logging.error("%s", e)
        raise

def get_select_query_result_dicts(sql_query, params=None):
    """Execute a query, return all rows for the query as list of dictionaries"""

    conn, cur = psql_connection()
    try:
        cur.execute(sql_query, params)
        columns = [desc[0] for desc in cur.description]  # Fetch column names
        result = [dict(zip(columns, row)) for row in cur.fetchall()]
        conn.close()
        return result
    except psycopg2.Error as e:
        logging.error("%s", e)
        raise

def get_hcpcs_locality_cost(hcpcs_code, locality_designation):
    """Get cost for a given hcpcs code and locality
    """

    sql_query = f"""
                SELECT
					codes_document ->> 'sdesc' AS short_description,
					codes_document ->> 'locality' AS mac_locality,
					codes_document ->> 'modifier' AS modifier,
					ROUND(CAST(codes_document ->> 'fac_price' AS numeric), 2) AS facility_price,
					ROUND(CAST(codes_document ->> 'nfac_price' AS numeric), 2) AS non_fasility_price,
					ROUND(CAST(codes_document ->> 'fac_limiting_charge' AS numeric), 2) AS facility_limiting_charge,
					ROUND(CAST(codes_document ->> 'nfac_limiting_charge' AS numeric), 2) AS non_facility_limiting_charge,
					codes_document ->> 'conv_fact' AS conv_fact
                FROM
					cpt_hcpcs_codes
                WHERE
					codes_document ->> 'hcpc' = '{hcpcs_code}'
					and codes_document ->> 'locality' = '{locality_designation}';
                """
    costs = get_select_query_result_dicts(sql_query)
    
    return costs

def get_pt_locality_and_codes(patient_document_id):
    """Get patient locality and associated codes

        Example:
            doc_id = 'aaf6b52080f87f01305a3de7f596e91354b3fec0969b0a870f560db9b11ba629667525285ab30886a51246035053e8211c7b7a75cd0d72a1ca4964785465764f'
            doc = get_pt_locality_and_codes(doc_id)

            for a_code in doc['codes']:
                print(a_code)
                est_costs = get_hcpcs_locality_cost(a_code, doc['locality'])
                print (est_costs)
    """
    
    sql_query = f"""
                SELECT 
                    pd.patient_id,
					pd.patient_locality,
                    jsonb_array_elements_text(pc.codes_document -> 'cpt' -> 'codes') AS cpt_code
                FROM 
                    public.patient_documents pd
                JOIN 
                    public.patient_codes pc ON pd.patient_document_id = pc.patient_document_id
                WHERE 
                    pd.patient_document_id = '{patient_document_id}';
                """
    locality_codes = get_select_query_result_dicts(sql_query)

    # Initialize the result dictionary
    result_dict = {}

    for item in locality_codes:
        patient_id = item['patient_id']
        locality = item['patient_locality']
        cpt_code = item['cpt_code']
    
        # If patient_id and locality are not yet in the result dictionary, initialize them
        if (patient_id, locality) not in result_dict:
            result_dict[(patient_id, locality)] = {'patient_id': patient_id, 'locality': locality, 'codes': []}
    
        # Append cpt_code to the codes list
        result_dict[(patient_id, locality)]['codes'].append(cpt_code)

    # Get the first item from the result dictionary
    pt_locality_codes = list(result_dict.values())[0]

    return pt_locality_codes

def get_icd_billable_estimates(patient_id):
    """Get billable information for icd codes for a given patient
    """

    sql_query = f"""
                SELECT
                    pc.patient_id,
                    icd_detail->>'code' AS code,
                    (icd_detail->>'billable')::boolean AS billable,
                    icd_detail->'full_data'->>'short_description' AS short_description,
                    icd_detail->'full_data'->'billing_guidelines'->'medical_provider'->>'reimbursement_rate' AS medical_provider_reimbursement_rate,
                    icd_detail->'full_data'->'billing_guidelines'->'insurance_company'->>'reimbursement_rate' AS insurance_company_reimbursement_rate,
                    pd.patient_locality
                FROM
                    patient_codes pc
                JOIN
                    jsonb_array_elements(pc.codes_document->'icd'->'details') AS icd_detail ON true
                JOIN
                    patient_documents pd ON pc.patient_id = pd.patient_id
                WHERE
                    pc.codes_document ? 'icd'
                    AND pc.patient_id = '{patient_id}';
                 """

    costs = get_select_query_result_dicts(sql_query)
    return costs

def get_cpt_fees(hcpcs_code, mac_locality):
    """Get locality based fee schedule for a given hcpcs code
    """

    sql_query = f"""
                    SELECT
                        codes_document ->> 'sdesc' AS short_description,
                        codes_document ->> 'locality' AS mac_locality,
                        codes_document ->> 'modifier' AS modifier,
                        codes_document ->> 'fac_price' AS facility_price,
                        codes_document ->> 'nfac_price' AS non_fasility_price,
                        codes_document ->> 'fac_limiting_charge' AS facility_limiting_charge,
                        codes_document ->> 'nfac_limiting_charge' AS non_facility_limiting_charge,
                        codes_document ->> 'conv_fact' AS conv_fact
                    FROM
                        cpt_hcpcs_codes
                    WHERE
                        codes_document ->> 'hcpc' = '{hcpcs_code}'
                        AND codes_document ->> 'locality' = '{mac_locality}';
                 """
    pass
