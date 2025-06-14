"""React Native app generation module using LLM."""

from dotenv import load_dotenv
from langchain_core.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from .prompt import PROMPT
from .llm_client import AppSpec, OpenRouterClient

load_dotenv()


def generate_app(user_request: str) -> str:
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

    return output.app_jsx
