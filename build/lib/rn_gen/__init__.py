"""React Native app generation module using LLM."""

import os
import random
import tempfile

from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from log import logger
from src.js_bundle_upload.main import build_app_local
from src.models import MiniApp
from src.supabase import supabase

from .prompt import EDITOR_PROMPT, METADATA_EDITOR_PROMPT, METADATA_PROMPT, PROMPT
from .utils import (
    AppMetadata,
    AppSpec,
    OpenRouterClient,
    insert_into_db,
    update_app_in_db,
)

load_dotenv()

llm = OpenRouterClient(model_name="anthropic/claude-sonnet-4")


def generate_app(user_request: str) -> AppSpec:
    """Generate React Native app JSX code based on user request.

    Args:
        user_request (str): The user's request for the app.

    Returns:
        str: The generated JSX code for the app.
    """
    with open(os.path.join(os.path.dirname(__file__), "prompt.txt"), "r") as file:
        p = file.read()

    prompt = PromptTemplate.from_template(PROMPT)
    parser = PydanticOutputParser(pydantic_object=AppSpec)

    chain = prompt | llm | parser

    output: AppSpec = chain.invoke(
        {
            "prompt": p,
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


def edit_app(user_request: str, previous_app_code: str) -> AppSpec:
    with open(os.path.join(os.path.dirname(__file__), "prompt.txt"), "r") as file:
        p = file.read()

    prompt = PromptTemplate.from_template(EDITOR_PROMPT)
    parser = PydanticOutputParser(pydantic_object=AppSpec)

    chain = prompt | llm | parser

    return chain.invoke(
        {
            "prompt": p,
            "user_request": user_request,
            "previous_app_code": previous_app_code,
            "format_instructions": parser.get_format_instructions(),
        }
    )


def edit_app_metadata(
    user_request: str,
    previous_app_metadata: AppMetadata,
) -> AppMetadata:
    prompt = PromptTemplate.from_template(METADATA_EDITOR_PROMPT)
    parser = PydanticOutputParser(pydantic_object=AppMetadata)

    chain = prompt | llm | parser

    return chain.invoke(
        {
            "user_request": user_request,
            "previous_app_metadata": previous_app_metadata,
            "format_instructions": parser.get_format_instructions(),
        }
    )


def build_and_upload_to_supabase(
    app_spec: AppSpec,
    app_metadata: AppMetadata,
) -> tuple[bool, str]:
    """Upload app specification to Supabase database.

    Args:
        app_spec (AppSpec): The app specification containing JSX code and metadata.

    Returns:
        bool: True if upload was successful, False otherwise.
        str: The deployment ID of the app if upload was successful, None otherwise.
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
        return success, result["buildId"]

    except Exception as e:
        logger.error(f"Error uploading to Supabase: {str(e)}")
        return False, None
    finally:
        temp_file.close()


def build_and_update_in_supabase(
    app_spec: AppSpec,
    app_metadata: AppMetadata,
    deployment_id: str,
) -> tuple[bool, str]:
    """Update existing app in Supabase database with new code and metadata.

    Args:
        app_spec (AppSpec): The updated app specification containing JSX code.
        app_metadata (AppMetadata): The updated app metadata.
        deployment_id (str): The deployment ID of the existing app to update.

    Returns:
        tuple[bool, str]: (True if update was successful, new deployment ID) or (False, None).
    """
    try:
        # Write a tempfile for App.jsx from app_spec
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(app_spec.app_jsx.encode("utf-8"))

        # Build the updated app
        result = build_app_local(app_spec.app_jsx)
        logger.info(result)

        new_deployment_id = result["buildId"]

        # Update the existing app in the database
        success = update_app_in_db(deployment_id, app_metadata, new_deployment_id)

        # Return success status and new deployment ID
        return success, new_deployment_id

    except Exception as e:
        logger.error(f"Error updating app in Supabase: {str(e)}")
        return False, None
    finally:
        temp_file.close()
