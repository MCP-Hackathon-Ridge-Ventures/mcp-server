from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI
import httpx
from pydantic import Field

from fastmcp import FastMCP

from src.rn_gen import build_and_upload_to_supabase, generate_app, generate_metadata

BACKEND_URL = "http://localhost:8001"
app = FastAPI(title="MicroApp")


@app.post("/create-app")
async def create_app_request(user_request: str):
    try:
        app_spec = generate_app(user_request)
        app_metadata = generate_metadata(user_request)
        success = build_and_upload_to_supabase(app_spec, app_metadata)
        return {"success": success}
    except Exception as e:
        return {"error": str(e)}


# FastMCP app
mcp = FastMCP(
    name="MicroApp",
    description="MicroApp is a platform for creating and sharing micro-apps.",
)


@mcp.tool()
async def generate_mobile_app(user_request: str) -> bool:
    """Generate an app based on user request.

    Args:
        user_request (str): The user's request for the app.

    Returns:
        bool: True if the app was generated successfully, False otherwise.
    """
    try:
        result = await create_app_request(user_request)
        return result.get("success", False)
    except Exception as e:
        print(f"Error generating app: {e}")
        return False


if __name__ == "__main__":
    print("Starting MicroApp...")
    mcp.run()
