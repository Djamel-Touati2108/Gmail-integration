import mysql.connector
from mysql.connector import Error

def creds_row_mapper(row):
    return {
        'cred_type':row[1],
        'user_id':row[2],
        'client_id':row[3],  
        'client_secret':row[4],
        'access_token':row[5],   
        'refresh_token':row[6] ,
        'expiry':row[7]
    }

def create_db_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name
        )
        print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")

    return connection

def read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as err:
        print(f"Error: '{err}'")

def execute_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        cursor.close()
        print("Query successful")
    except Error as err:
        print(f"Error: '{err}'")

def save_creds_query(cred_type,user_id,client_id,client_secret,access_token,refresh_token ,expiry):
    a="""
    INSERT INTO
            creds(
                cred_type,
                user_id,
                client_id,  
                client_secret,
                access_token,   
                refresh_token ,
                expiry
            )
        VALUES (
            '{}',
            '{}',
            '{}',
            '{}',
            '{}',
            '{}',
            '{}' )
    """.format(cred_type,user_id,client_id,client_secret,access_token,refresh_token,expiry)

    return str(a)

def get_creds_query(cred_type):
    return """
    Select * from creds WHERE 
    cred_type = '{}'
    """.format(cred_type)

def update_creds_query(access_token,refresh_token,expiry,cred_type):
    return """
     UPDATE 
            creds
     SET
            access_token  = '{}',
            refresh_token = '{}',
            expiry = '{}'
     WHERE 
            cred_type = '{}'
    """.format(access_token,refresh_token,expiry,cred_type)

def delete_creds_query(cred_type):
    return """
      DELETE FROM
            creds
        WHERE 
            cred_type = '{}'
    """.format(cred_type)
