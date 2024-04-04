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

def get_select_query_result_dicts(sql_query):
    """Execute a query, return all rows for the query as list of dictionaries"""

    conn, cur = psql_connection()
    try:
        cur.execute(sql_query)
        columns = [desc[0] for desc in cur.description]  # Fetch column names
        result = [dict(zip(columns, row)) for row in cur.fetchall()]
        conn.close()
        return result
    except psycopg2.Error as e:
        logging.error("%s", e)
        raise

def get_new_data_ids(table_name, unique_column, reddit_data):
    """Get object ids for new messages on reddit
        query db for existing ids
        query api for all ids
        return the diff from the api
    """

    query = f"""SELECT {unique_column} FROM {table_name} GROUP BY {unique_column};"""

    data_ids_db = [] # array to hold ids from database table
    data_ids_reddit = [] # arrary to hold ids from reddit api call

    result = get_select_query_results(query)
    for row in result:
        data_ids_db.append(row[0])

    for item in reddit_data:
        data_ids_reddit.append(item.id)

    new_list = set(data_ids_reddit) - set(data_ids_db)
    #TODO new_list_of_lists = list(list_into_chunks(list(newlist), NUM_ELEMENTS_CHUNK))
    return list(new_list)

def db_get_authors():
    """Get list of authors from db table
        return python list
    """

    author_list = []
    query = """SELECT author_name FROM author GROUP BY author_name;"""
    authors = get_select_query_results(query)
    for row in authors:
        author_list.append(row[0])
    return author_list

def db_get_post_ids():
    """List of post_ids, filtering out pre-analyzed post_ids from this
    """

    post_id_list = []
    sql_query = """SELECT post_id
                   FROM post
                   WHERE post_body NOT IN ('', '[removed]', '[deleted]')
                   AND post_id NOT IN (SELECT analysis_document ->> 'post_id' AS pid
                                       FROM analysis_documents
                                       WHERE analysis_document ->> 'post_id' IS NOT NULL
                                       GROUP BY pid);"""
    post_ids = get_select_query_results(sql_query)
    if not post_ids:
        logging.warning("db_get_post_ids(): no post_ids found in DB")
        return

    for a_post_id in post_ids:
        post_id_list.append(a_post_id[0])

    return post_id_list

def db_get_comment_ids():
    """List of post_ids, filtering out pre-analyzed post_ids from this
    """

    comment_id_list = []
    sql_query = """SELECT comment_id
                   FROM comment
                   WHERE comment_body NOT IN ('', '[removed]', '[deleted]')
                   AND comment_id NOT IN (SELECT analysis_document ->> 'comment_id' AS pid
                                          FROM analysis_documents
                                          WHERE analysis_document ->> 'comment_id' is NOT null
                                          GROUP BY pid);"""
    comment_ids = get_select_query_results(sql_query)
    if not comment_ids:
        logging.warning("db_get_comment_ids(): no post_ids found in DB")
        return

    for a_comment_id in comment_ids:
        comment_id_list.append(a_comment_id[0])

    return comment_id_list

def get_hcpcs_locality_cost(hcpcs_code, locality_designation):
    """_summary_

    Args:
        hcpcs_code (_type_): _description_
        locality_designation (_type_): _description_
    """

    sql_query = f"""
                select
	                codes_document ->> 'sdesc' as short_description,
	                codes_document ->> 'locality' as mac_locality,
	                codes_document ->> 'modifier' as modifier,
	                round(cast(codes_document ->> 'fac_price' as numeric), 2) as facility_price,
	                round(cast(codes_document ->> 'nfac_price' as numeric), 2) as non_fasility_price,
	                round(cast(codes_document ->> 'fac_limiting_charge' as numeric), 2) as facility_limiting_charge,
	                round(cast(codes_document ->> 'nfac_limiting_charge' as numeric), 2)as non_facility_limiting_charge,
	                codes_document ->> 'conv_fact' as conv_fact
                from
	                cpt_hcpcs_codes
                where
	                codes_document ->> 'hcpc' = '{hcpcs_code}'
	                and codes_document ->> 'locality' = '{locality_designation}';
                 """
    costs = get_select_query_result_dicts(sql_query)
    
    return costs

def get_pt_locality_and_codes(patient_document_id):
    """

    Args:
        patient_document_id (_type_): _description_
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
#doc_id = 'aaf6b52080f87f01305a3de7f596e91354b3fec0969b0a870f560db9b11ba629667525285ab30886a51246035053e8211c7b7a75cd0d72a1ca4964785465764f'
#doc = get_pt_locality_and_codes(doc_id)

#for a_code in doc['codes']:
#    print(a_code)
#    est_costs = get_hcpcs_locality_cost(a_code, doc['locality'])
#    print (est_costs)
