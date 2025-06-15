"""React Native app generation module using LLM."""

import os
from dotenv import load_dotenv
from langchain_core.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from .prompt import PROMPT
from .utils import AppSpec, OpenRouterClient

load_dotenv()


def generate_app(user_request: str) -> AppSpec:
    """Generate React Native app JSX code based on user request.

    Args:
        user_request (str): The user's request for the app.

    Returns:
        str: The generated JSX code for the app.
    """
    llm = OpenRouterClient(model_name="anthropic/claude-sonnet-4")
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


def upload_to_supabase(app_spec: AppSpec) -> bool:
    """Upload app specification to Supabase database.

    Args:
        app_spec (AppSpec): The app specification containing JSX code and metadata.

    Returns:
        bool: True if upload was successful, False otherwise.
    """
    try:
        # TODO: Implement step 1 - Get deployment ID from API

        data = {
            "name": app_spec.name,
            "description": app_spec.description,
            "deployment_id": deployment_id,  # Will be set after step 1
            "jsx_code": app_spec.app_jsx,
        }

        result = supabase.table("apps").insert(data).execute()

        # Step 3: Return success status
        return result.data is not None

    except Exception as e:
        print(f"Error uploading to Supabase: {str(e)}")
        return False
