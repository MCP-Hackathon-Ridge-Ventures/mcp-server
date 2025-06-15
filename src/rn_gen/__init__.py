"""React Native app generation module using LLM."""

import os
from dotenv import load_dotenv
from langchain_core.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from src.js_bundle_upload.main import build_app_local
from .prompt import PROMPT, METADATA_PROMPT
from .utils import AppSpec, OpenRouterClient, AppMetadata
from src.supabase import supabase
import tempfile
import random

load_dotenv()

llm = OpenRouterClient(model_name="anthropic/claude-sonnet-4")


def generate_app(user_request: str) -> AppSpec:
    """Generate React Native app JSX code based on user request.

    Args:
        user_request (str): The user's request for the app.

    Returns:
        str: The generated JSX code for the app.
    """
    prompt = PromptTemplate.from_template(PROMPT)
    parser = PydanticOutputParser(pydantic_object=AppSpec)

    chain = prompt | llm | parser

    output: AppSpec = chain.invoke(
        {
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
        print(result)

        data = {
            "name": app_metadata.name,
            "description": app_metadata.description,
            "category": app_metadata.category,
            "tags": app_metadata.tags,
            "deployment_id": result["buildId"],  # Will be set after step 1,
            "icon_url": None,
            "version": "1.0.0",
            # Generate a random rating between 4.1 and 5
            "rating": round(random.uniform(4.1, 5), 1),
            "downloads": 1,
            "is_featured": False,
        }

        result = supabase.table("mini_apps").insert(data).execute()

        # Step 3: Return success status
        return result.data is not None

    except Exception as e:
        print(f"Error uploading to Supabase: {str(e)}")
        return False
    finally:
        temp_file.close()
