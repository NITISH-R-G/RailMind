import logging
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger

def get_json_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    import os
    if not os.path.exists("logs"):
        os.makedirs("logs", exist_ok=True)

    logHandler = RotatingFileHandler('logs/railmind.log', maxBytes=10*1024*1024, backupCount=5)
    formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    logHandler.setFormatter(formatter)

    logger.addHandler(logHandler)
    return logger
