import mysql.connector
import pandas as pd

class MySqlConnector:
    """Handles MySQL connection and query execution."""
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database

    def get_connection(self):
        try:
            return mysql.connector.connect(
                host=self.host, user=self.user,
                password=self.password, database=self.database
            )
        except mysql.connector.Error as e:
            print("Connection failed:", e)
            return None

    def execute_pd_query(self, query):
        try:
            conn = self.get_connection()
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            return f"Error: {e}"

    def execute_sql_query(self, query):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            return f"Error: {e}"

    def get_basic_info(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        schema = {}
        for (table,) in tables:
            cursor.execute(f"DESCRIBE {table}")
            schema[table] = cursor.fetchall()
        cursor.close()
        conn.close()
        return schema
