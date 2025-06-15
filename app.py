import asyncio
import traceback

from enrichmcp import EnrichMCP
from fastmcp import FastMCP
from fastapi import FastAPI
from log import logger
from src.rn_gen import (
    build_and_update_in_supabase,
    build_and_upload_to_supabase,
    edit_app,
    edit_app_metadata,
    generate_app,
    generate_metadata,
)
from src.supabase import download_from_bucket
from src.supabase import supabase as supabase_client

BACKEND_URL = "http://localhost:8001"
app = FastAPI(title="MicroApp")


async def generate_app_wrapper(user_request: str) -> dict:
    try:
        app_spec = generate_app(user_request)
        app_metadata = generate_metadata(user_request)
        success, deployment_id = build_and_upload_to_supabase(app_spec, app_metadata)
        return {"success": success, "deployment_id": deployment_id}
    except Exception as e:
        return {"error": str(e)}


async def edit_app_wrapper(user_request: str, deployment_id: str) -> dict:
    try:
        previous_app_code = download_from_bucket(f"{deployment_id}/app.jsx")
        previous_app_metadata = (
            supabase_client.table("mini_apps")
            .select("description, category, tags")
            .eq("deployment_id", deployment_id)
            .execute()
            .data[0]
        )

        app_spec = edit_app(user_request, previous_app_code)
        app_metadata = edit_app_metadata(user_request, previous_app_metadata)
        success, new_deployment_id = build_and_update_in_supabase(
            app_spec, app_metadata, deployment_id
        )

        return {
            "success": success,
            "new_deployment_id": new_deployment_id,
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/create-app")
async def create_app_request(user_request: str):
    return await generate_app_wrapper(user_request)


# EnrichMCP app
mcp = EnrichMCP(
    "MicroApp",
    description="Mobile app generation service",
)


@mcp.resource()
async def generate_mobile_app(user_request: str) -> dict[str, str]:
    """This is a tool to generate a mobile app based on any user request. If a user asks for a mobile app, this tool will be used to generate the app.
    The mobile app will be generated using the user request and the app will be sent to the user's phone.
    Please notify the user that the app is being generated and will be sent to their phone soon.
    """
    try:
        result = await generate_app_wrapper(user_request)
        return {
            "message": "App generated successfully",
            "result": str(result),
        }
    except Exception as e:
        print("--------------------------------")
        print(f"Error generating app: {e}")
        print(traceback.format_exc())
        return {
            "message": "Error generating app",
            "error": str(e),
        }


@mcp.resource()
async def edit_mobile_app(user_request: str, deployment_id: str) -> dict[str, str]:
    """This is a tool to edit a mobile app based on any user request. If a user asks for a mobile app, this tool will be used to edit the app.
    The mobile app will be edited using the user request and the app will be sent to the user's phone.
    Please notify the user that the app is being edited and will be sent to their phone soon.
    """
    try:
        result = await edit_app_wrapper(user_request, deployment_id)
        return {
            "message": "App edited successfully",
            "result": str(result),
        }
    except Exception as e:
        print("--------------------------------")
        print(f"Error editing app: {e}")
        print(traceback.format_exc())
        return {
            "message": "Error editing app",
            "error": str(e),
        }


if __name__ == "__main__":
    logger.info("Starting MicroApp...")
    mcp.run()
