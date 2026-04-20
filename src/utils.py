import logging
from logging import Logger
import os
import json

from src import constants


def init__logger(file_name: str,
                 log_format: str = None,
                 mode: str = "w",
                 debug_level: bool = False) -> Logger:
    """
    """
    if log_format is None:
        log_format = "%(asctime)s | %(levelname)-8s  | %(funcName)s#L-%(lineno)d | %(message)s"

    logger = logging.getLogger(file_name)
    if debug_level:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(os.path.join(constants.BASE_DIR, file_name), mode=mode)
    formatter = logging.Formatter(log_format)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger


def save_json(file_path: str, data: dict | list) -> str:
    """
    """
    json_str = json.dumps(data, ensure_ascii=False, indent=4)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(json_str)
    return file_path
