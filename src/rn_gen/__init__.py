"""React Native app generation module using LLM."""

import os
import random
import tempfile

from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from src.js_bundle_upload.main import build_app_local
from src.models import MiniApp
from src.supabase import supabase
from log import logger
from .prompt import METADATA_PROMPT, PROMPT
from .utils import AppMetadata, AppSpec, OpenRouterClient, insert_into_db

load_dotenv()

llm = OpenRouterClient(model_name="anthropic/claude-sonnet-4")


def generate_app(user_request: str) -> AppSpec:
    """Generate React Native app JSX code based on user request.

    Args:
        user_request (str): The user's request for the app.

    Returns:
        str: The generated JSX code for the app.
    """
    with open("src/rn_gen/prompt.txt", "r") as file:
        prompt = file.read()

    prompt = PromptTemplate.from_template(PROMPT)
    parser = PydanticOutputParser(pydantic_object=AppSpec)

    chain = prompt | llm | parser

    output: AppSpec = chain.invoke(
        {
            "prompt": prompt,
            "user_request": user_request,
            "format_instructions": parser.get_format_instructions(),
        }
    )

    return output


def generate_metadata(user_request: str) -> dict:
    prompt = PromptTemplate.from_template(METADATA_PROMPT)
    parser = PydanticOutputParser(pydantic_object=AppMetadata)

    chain = prompt | llm | parser

    output: AppSpec = chain.invoke(
        {
            "user_request": user_request,
            "format_instructions": parser.get_format_instructions(),
        }
    )

    return output


def build_and_upload_to_supabase(app_spec: AppSpec, app_metadata: AppMetadata) -> bool:
    """Upload app specification to Supabase database.

    Args:
        app_spec (AppSpec): The app specification containing JSX code and metadata.

    Returns:
        bool: True if upload was successful, False otherwise.
    """
    try:
        # Write a tempfile for App.jx from app_spec
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(app_spec.app_jsx.encode("utf-8"))

        result = build_app_local(app_spec.app_jsx)
        logger.info(result)

        # Create a MiniApp object
        mini_app = MiniApp(
            name=app_metadata.name,
            description=app_metadata.description,
            category=app_metadata.category,
            tags=app_metadata.tags,
            deployment_id=result["buildId"],
            icon_url=app_metadata.app_icon,
            version="1.0.0",
            rating=round(random.uniform(4.1, 5), 1),
            downloads=1,
            is_featured=random.random() < 0.3,
        )

        # Insert into DB
        success = insert_into_db(mini_app)

        # Step 3: Return success status
        return success

    except Exception as e:
        logger.error(f"Error uploading to Supabase: {str(e)}")
        return False
    finally:
        temp_file.close()
