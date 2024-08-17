import json
import time
import traceback
from typing import Any, NoReturn
import os
import psycopg2


class PostgreSQL:
    def __init__(self):
        self.connection = psycopg2.connect(dbname=os.getenv("POSTGRES_DB_NAME"), user=os.getenv("POSTGRES_USER"),
                                           password=os.getenv("POSTGRES_PASSWORD"), host=os.getenv("HOST"))

    def __del__(self):
        try:
            self.close_connection()
        except AttributeError:
            pass

    def execute_query_with_results(self, query: str, values: list | None = None, retry=0) -> list:
        cursor = self.connection.cursor()
        try:
            if values:
                values = [json.dumps(v, default=str) if isinstance(v, dict) else v for v in values]
                cursor.execute(query, values)
            else:
                cursor.execute(query)
            column_names = [desc[0] for desc in cursor.description]
            rows = []
            for row in cursor.fetchall():
                row_dict = dict(zip(column_names, row))
                rows.append(row_dict)
            self.connection.commit()
            cursor.close()
            return rows
        except psycopg2.Error as e:
            print(query, values)
            cursor.execute('rollback')
            cursor.close()
            print(f"Error executing query with results: {e}")
            print(traceback.format_exc())
            time.sleep(3)
            if retry < 3:
                return self.execute_query_with_results(query, values, retry + 1)
            else:
                raise Exception("Error executing query with results: " + traceback.format_exc())

    def close_connection(self):
        self.connection.close()


class PostgreSQLTable:
    def __init__(self, table_name):
        self.table_name = table_name
        self.db = PostgreSQL()

    def insert_row(self, data: dict, retry: int = 0) -> dict | None:
        try:
            column_names = ", ".join(data.keys())
            values = list(data.values())
            placeholders = ", ".join(["%s"] * len(values))
            query = f"INSERT INTO {self.table_name} ({column_names}) VALUES ({placeholders}) RETURNING *"
            inserted_row = self.db.execute_query_with_results(query, values)
            self.db.connection.commit()
            if inserted_row:
                return inserted_row[0]
            else:
                return None
        except Exception:
            print(traceback.format_exc())
            time.sleep(3)
            if retry < 3:
                return self.insert_row(data, retry + 1)
            else:
                raise Exception("Error updating row: " + traceback.format_exc())

    def update_row(self, custom_field: str, custom_value: Any, data: dict, retry: int = 0) -> dict | None:
        try:
            set_columns = ", ".join([f"{column} = %s" for column in data.keys()])

            set_values = list(data.values())
            condition = f"{custom_field} = %s"
            condition_value = [custom_value]
            query = f"UPDATE {self.table_name} SET {set_columns} WHERE {condition} RETURNING *"
            updated_row = self.db.execute_query_with_results(query, set_values + condition_value)
            self.db.connection.commit()
            if updated_row:
                return updated_row[0]
            else:
                return None
        except Exception:
            print(traceback.format_exc())
            time.sleep(3)
            if retry < 3:
                return self.update_row(custom_field, custom_value, data, retry + 1)
            else:
                raise Exception("Error updating row: " + traceback.format_exc())

    def delete_row(self, condition_field: str, condition_value: Any, retry: int = 0) -> None:
        try:
            query = f"DELETE FROM {self.table_name} WHERE {condition_field} = %s RETURNING *"
            self.db.execute_query_with_results(query, [condition_value])
            self.db.connection.commit()
        except Exception:
            time.sleep(3)
            if retry < 3:
                return self.delete_row(condition_field, condition_value, retry + 1)
            else:
                raise Exception("Error updating row: " + traceback.format_exc())

    def get_all_rows(self, retry: int = 0) -> list | NoReturn:
        cursor = self.db.connection.cursor()
        try:
            query = f"SELECT * FROM {self.table_name} order by id"
            cursor.execute(query)
            column_names = [desc[0] for desc in cursor.description]
            rows = []
            for row in cursor.fetchall():
                row_dict = dict(zip(column_names, row))
                rows.append(row_dict)
            cursor.close()
            self.db.connection.commit()

            return rows
        except Exception:
            cursor.execute('rollback')
            print(traceback.format_exc())
            time.sleep(3)
            if retry < 3:
                return self.get_all_rows()
            else:
                raise Exception("Error updating row: " + traceback.format_exc())

    def get_row(self, condition_field: str, condition_value: Any, retry: int = 0) -> dict | None:
        cursor = self.db.connection.cursor()
        try:
            query = f"SELECT * FROM {self.table_name} WHERE {condition_field} = %s"
            cursor.execute(query, (condition_value,))
            results = cursor.fetchall()
            cursor.close()
            if results:
                row_data = results[0]
                column_names = [desc[0] for desc in cursor.description]
                row_dict = {column: value for column, value in zip(column_names, row_data)}
                return row_dict
            else:
                return None

        except Exception:
            cursor.execute('rollback')
            print(traceback.format_exc())
            time.sleep(3)
            if retry < 3:
                return self.get_row(condition_field, condition_value, retry + 1)
            else:
                raise Exception("Error updating row: " + traceback.format_exc())

    def get_rows_with_filter(self, condition_field: str, condition_value: Any, retry: int = 0) -> list | NoReturn:
        cursor = self.db.connection.cursor()
        try:
            query = f"SELECT * FROM {self.table_name} WHERE {condition_field} = %s"
            cursor.execute(query, (condition_value,))
            column_names = [desc[0] for desc in cursor.description]
            rows = []
            for row in cursor.fetchall():
                row_dict = dict(zip(column_names, row))
                rows.append(row_dict)
            cursor.close()
            self.db.connection.commit()

            return rows
        except Exception:
            cursor.execute('rollback')
            print(traceback.format_exc())
            time.sleep(3)
            if retry < 3:
                return self.get_rows_with_filter(condition_field, condition_value, retry + 1)
            else:
                raise Exception("Error updating row: " + traceback.format_exc())