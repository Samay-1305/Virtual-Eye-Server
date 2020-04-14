import threading
import socket
import json

class Server:
    def __init__(self, server_config_file="server_config.json"):
        self.__server_config_file = server_config_file
        with open(server_config_file, "r") as config_file_object:
            self.__server_config = json.loads(config_file_object.read())
        self.__serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__serv.bind((self.__server_config["host"], self.__server_config["port"]))
        self.__thread = threading.Thread(target=self.__function_thread)
        self.__connected_clients = {}

    def __function_thread(self):
        pass

    def close(self):
        for client_id in self.__connected_clients.keys():
            self.__connected_clients[client_id]["connection"].close()
        self.__serv.close()