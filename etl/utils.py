import logging
import os

from config import get_log_path


def set_logger(fase):
    logger = logging.getLogger(fase)
    logger.setLevel(logging.DEBUG)

    if logger.hasHandlers():
        logger.handlers.clear()

    log_path = get_log_path(fase)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
