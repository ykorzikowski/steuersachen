import os
import logging

DEBUG = int(os.getenv('DEBUG', "1"))
LOG_TO_FILE = int(os.getenv('LOG_TO_FILE', default=0)) == 1

class Logger:
    @staticmethod
    def get_logger():
        return logging.getLogger('wealthbuddy')

    @staticmethod
    def configure_logger():
        logging_format = '%(asctime)s - %(levelname)s - %(name)s - %(threadName)s - %(funcName)s():%(lineno)d - %(message)s'
        if LOG_TO_FILE:
            logging.basicConfig(filename='wealthbuddy.log', level=logging.INFO, format=logging_format)
        else:
            logging.basicConfig(level=logging.INFO, format=logging_format)
        if DEBUG > 0:
            logging.basicConfig(level=logging.DEBUG, format=logging_format)
        if DEBUG > 0:
            Logger.get_logger().setLevel(logging.DEBUG)