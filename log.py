from dotenv import load_dotenv

load_dotenv()

import logging
import os

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=os.path.join(os.path.dirname(__file__), "logs", "app.log"),
    filemode="a",
)
logger = logging.getLogger(__name__)
