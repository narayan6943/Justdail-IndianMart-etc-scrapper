import logging
import os
from datetime import datetime
from .config import config

def setup_logger():
    log_dir = config.log_file.parent
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger("Scraper")
    logger.setLevel(getattr(logging, config.settings['logging']['level'].upper()))
    
    # File Handler
    fh = logging.FileHandler(config.log_file)
    fh_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(fh_formatter)
    
    # Console Handler
    ch = logging.StreamHandler()
    ch_formatter = logging.Formatter('%(levelname)s: %(message)s')
    ch.setFormatter(ch_formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

logger = setup_logger()

def timestamp():
    return datetime.now().isoformat()
