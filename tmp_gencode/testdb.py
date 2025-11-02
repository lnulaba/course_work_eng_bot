# mysql remote connection
import mysql.connector
from mysql.connector import Error

def create_connection():
    """ create a database connection to the MySQL database """
    connection = None
    try:
        connection = mysql.connector.connect(
            host="31.222.235.200",
            user="gkevzmyh_martha",
            password="oC7xQ9cS5e",
            database="gkevzmyh_eng_courses"
        )
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

def close_connection(connection):
    """ close the database connection """
    if connection:
        connection.close()
        print("The connection is closed")

if __name__ == "__main__":
    conn = create_connection()
    close_connection(conn)