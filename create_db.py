import mysql.connector
from mysql.connector import Error

#EXECUTE THIS SCRIPT ONLY FIRST TIME YOU RUN THIS PROJECT 
#YOU NEED MY SQL SERVER TO RUN THIS SCRIPT

def create_server_connection(host_name, user_name, user_password):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password
        )
        print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")

    return connection

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

def create_database(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        print("Database created successfully")
    except Error as err:
        print(f"Error: '{err}'")

def execute_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print("Query successful")
    except Error as err:
        print(f"Error: '{err}'")

connection = create_server_connection("localhost", "root", "My3QlP@ssword")

create_database_query="CREATE DATABASE Credentials"

execute_query(connection,create_database_query)


create_token_table = """
CREATE TABLE creds (
  cred_id INT PRIMARY KEY AUTO_INCREMENT,
  cred_type VARCHAR(50) NOT NULL,
  user_id VARCHAR(255) NOT NULL,
  client_id VARCHAR(255) NOT NULL,
  client_secret VARCHAR(255) NOT NULL,
  access_token VARCHAR(255) NOT NULL,
  refresh_token VARCHAR(255) NOT NULL,
  expiry VARCHAR(255) NOT NULL
  );
 """

connection = create_db_connection("localhost", "root", "My3QlP@ssword", "Credentials") # Connect to the Database
execute_query(connection, create_token_table) # Execute our defined query