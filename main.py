# Virtual Eye Server V2.1
CLASSIFIER_CONFIG_FILE = "config//image_classifier_config.json"
DATABASE_CONFIG_FILE = "config//database_config.json"
SERVER_CONFIG_FILE = "config//server_config.json"

from server_modules import classifiers
from server_modules import functions
from server_modules import database
from server_modules import network

if __name__ == "__main__":
    clf = classifiers.ImageClassifier(CLASSIFIER_CONFIG_FILE)
    storage = database.SQLite3(DATABASE_CONFIG_FILE)
    server = network.Server(SERVER_CONFIG_FILE)
    handler = functions.MainHandler()
    handler.set_sources(
        server=server,
        classifier=clf,
        storage=storage
    )
    handler.start()
    handler.shutdown()