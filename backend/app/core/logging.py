import logging
import sys
from app.core.config import settings

def setup_logging():
    """
    Configures the root logger to output structured-ish logs to stdout.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Remove existing handlers to avoid duplicates during reloads
    logger.handlers = []
    logger.addHandler(handler)
    
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").addHandler(handler)
    
    return logger

logger = setup_logging()
