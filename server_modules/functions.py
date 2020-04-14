import threading

class MainHandler:
    def __init__(self):
        self.__server = None
        self.__classifier = None
        self.__storage = None
        
    def set_sources(self, server=None, classifier=None, storage=None):
        self.__server = server
        self.__classifier = classifier
        self.__storage = storage

    def start(self):
        pass

    def __function_thread(self):
        pass

    def shutdown(self):
        self.__server.close()
        self.__storage.close()