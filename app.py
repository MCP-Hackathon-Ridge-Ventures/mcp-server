from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI
import asyncio
import httpx
from pydantic import Field

from log import logger

from fastmcp import FastMCP

from src.rn_gen import build_and_upload_to_supabase, generate_app, generate_metadata

BACKEND_URL = "http://localhost:8001"
app = FastAPI(title="MicroApp")


async def generate_app_wrapper(user_request: str) -> dict:
    try:
        app_spec = generate_app(user_request)
        app_metadata = generate_metadata(user_request)
        success = build_and_upload_to_supabase(app_spec, app_metadata)
        return {"success": success}
    except Exception as e:
        return {"error": str(e)}


@app.post("/create-app")
async def create_app_request(user_request: str):
    return await generate_app_wrapper(user_request)


# FastMCP app
mcp = FastMCP(name="MicroApp", log_level="CRITICAL")


@mcp.tool()
async def generate_mobile_app(user_request: str) -> bool:
    """This is a tool to generate a mobile app based on any user request. If a user asks for a mobile app, this tool will be used to generate the app.
    The mobile app will be generated using the user request and the app will be sent to the user's phone.
    Please notify the user that the app is being generated and will be sent to their phone soon.
    """
    try:
        result = await generate_app_wrapper(user_request)
        return result.get("success", False)
    except Exception as e:
        logger.error(f"Error generating app: {e}")
        return False


if __name__ == "__main__":
    logger.info("Starting MicroApp...")
    asyncio.run(mcp.run(transport="stdio"))
