from dotenv import load_dotenv

load_dotenv()

import logging
import os

# Create logs directory if it doesn't exist
os.makedirs(os.path.join(os.path.dirname(__file__), "logs"), exist_ok=True)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=os.path.join(os.path.dirname(__file__), "logs", "app.log"),
    filemode="a",
)
logger = logging.getLogger(__name__)
