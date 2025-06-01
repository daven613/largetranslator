print("Hello from tiny_test.py")
import logging
logging.basicConfig(level=logging.INFO)
logging.info("Logging from tiny_test.py")
logger = logging.getLogger(__name__)
logger.info("Logger getLogger from tiny_test.py")
