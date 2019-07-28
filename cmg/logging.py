import logging
import sys


class LogLevel:
    Debug = logging.DEBUG
    Info = logging.INFO
    Warning = logging.WARNING
    Error = logging.ERROR
    Critical = logging.CRITICAL


def get_logger(name):
    logger = logging.getLogger(name)
    return logger


def create_logger(name, stdout=True, log_file=None, level=LogLevel.Debug):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if stdout:
        handler = logging.StreamHandler(sys.stdout)
        logger.addHandler(handler)
    if log_file is not None:
        handler = logging.FileHandler(log_file)
        logger.addHandler(handler)
    return logger
