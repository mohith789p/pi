import logging
from logging.handlers import RotatingFileHandler
from utils.fs import safe_mkdir
from pathlib import Path

def setup_logger(log_dir="logs"):
    safe_mkdir(Path(log_dir))
    try:
        file_handler = RotatingFileHandler(f"{log_dir}/henguard.log", maxBytes=2*1024*1024, backupCount=3)
        handlers = [file_handler, logging.StreamHandler()]
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=handlers
        )
    except Exception as e:
        print(f"Logger setup failed: {e}. Falling back to console logging.")
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s"
        )
    return logging.getLogger("HenGuard")