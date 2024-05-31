import os
import logging

_LOG_FMT = '%(asctime)s - %(levelname)s - %(name)s -   %(message)s'
_DATE_FMT = '%m/%d/%Y %H:%M:%S'
logging.basicConfig(format=_LOG_FMT, datefmt=_DATE_FMT, level=logging.INFO)
LOGGER = logging.getLogger('__main__')  # this is the global logger

def add_log_to_file(log_path):
    dirname = os.path.dirname(log_path)
    if not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)
    fh = logging.FileHandler(log_path)
    formatter = logging.Formatter(_LOG_FMT, datefmt=_DATE_FMT)
    fh.setFormatter(formatter)
    LOGGER.addHandler(fh)