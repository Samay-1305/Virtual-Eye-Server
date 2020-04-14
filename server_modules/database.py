import threading
import sqlite3
import json

class SQLite3:
    def __init__(self, database_config_file="database_config.json"):
        self.__database_config_file = database_config_file
        with open(database_config_file, "r") as config_file_object:
            self.__database_config = json.loads(config_file_object.read())
        self.__querys = {}
        self.__query_results = {}
        self.__querys_no_result = []
        self.__query_count = 0
        self.__database_is_running = True
        self.__thread = threading.Thread(target=self.__function_thread)
        self.__thread.setDaemon = True
        self.__thread.start()

    def __function_thread(self):
        self.__database_connection = sqlite3.connect(self.__database_config["file_path"])
        self.__database_cursor = self.__database_connection.cursor()
        for table_name in self.__database_config["tables"].keys():
            column_querys = ", ".join(" ".join(map(str, column_data)) for column_data in self.__database_config["tables"][table_name])
            query = "CREATE TABLE IF NOT EXISTS {} ({});".format(table_name, column_querys)
        self.__database_connection.commit()
        while (self.__database_is_running):
            for query_id in self.__querys.keys():
                result = self.__execute(self.__querys[query_id])
                self.__query_results[query_id] = result
            for query in self.__querys_no_result:
                self.__execute_no_result(query)
            self.__querys_no_result = []
        self.__database_cursor.close()
        self.__database_connection.close()

    def __execute(self, query):
        try:
            self.__database_cursor.execute(query)
            query_result = self.__database_cursor.fetchall()
        except Exception as DatabaseException:
            print(DatabaseException)
            query_result = None
        return query_result

    def __execute_no_result(self, query):
        try:
            self.__database_cursor.execute(query)
            self.__database_connection.commit()
        except Exception as DatabaseException:
            print(DatabaseException)

    def add_query(self, query):
        query_id = self.__query_count
        self.__querys[query_id] = str(query)
        self.__query_count += 1
        return query_id

    def add_query_no_result(self, query):
        self.__querys_no_result.append(query)

    def get_result(self, query_id):
        while query_id not in self.__query_results.keys():
            pass
        result = self.__query_results.pop(query_id)
        del self.__querys[query_id]
        return result

    def close(self):
        self.__database_is_running = False
        self.__thread.join()