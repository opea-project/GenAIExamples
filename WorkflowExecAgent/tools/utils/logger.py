import logging
import functools

def get_logger(name=None):
    logger = logging.getLogger(name)

    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)s - %(funcName)s - %(asctime)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
