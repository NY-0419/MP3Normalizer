import logging
from settings import get_app_data_dir

def setup_logger(log_file=None):
    logger = logging.getLogger("MP3VolumeNormalizer")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        log_path = get_app_data_dir() / (log_file or "app.log")
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger
