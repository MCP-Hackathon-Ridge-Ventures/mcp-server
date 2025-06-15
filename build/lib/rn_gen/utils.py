"""LLM client and data models for React Native app generation."""

import os
from typing import Optional

from dotenv import load_dotenv
from langchain_core.utils.utils import secret_from_env
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, SecretStr
from sqlalchemy.exc import SQLAlchemyError
from src.models import MiniApp
from src.supabase import session

from log import logger

load_dotenv()


class OpenRouterClient(ChatOpenAI):
    """OpenRouter API client for LLM interactions."""

    openai_api_key: Optional[SecretStr] = Field(
        alias="api_key",
        default_factory=secret_from_env("OPENROUTER_API_KEY", default=None),
    )

    @property
    def lc_secrets(self) -> dict[str, str]:
        return {"openai_api_key": "OPENROUTER_API_KEY"}

    def __init__(self, openai_api_key: Optional[str] = None, **kwargs):
        openai_api_key = openai_api_key or os.environ.get("OPENROUTER_API_KEY")
        super().__init__(
            base_url="https://openrouter.ai/api/v1",
            openai_api_key=openai_api_key,
            **kwargs,
        )


class AppSpec(BaseModel):
    """Data model for app specification containing JSX code."""

    app_jsx: str = Field(description="The JSX code for the app")


class AppMetadata(BaseModel):
    """Data model for app metadata."""

    name: str = Field(description="The name of the app")
    description: str = Field(description="The description of the app")
    category: str = Field(
        description="A single value of the category of the app. Examples include Health, Design, Productivity, Utilities, etc."
    )
    app_icon: str = Field(description="An emoji that best represents the app")
    tags: list[str] = Field(
        description="The set of three tags of the app. Examples include [Weather, Forecast, Location], [Todo, Tasks, Productivity], etc."
    )


def insert_into_db(mini_app: MiniApp) -> bool:
    """Insert a MiniApp object into the database."""
    success = False

    try:
        session.add(mini_app)
        session.commit()
        success = True
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Insertion failed: {str(e)}")
    finally:
        session.close()

    return success
