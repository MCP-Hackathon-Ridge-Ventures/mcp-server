from fastapi import FastAPI, BackgroundTasks
from src.rn_gen import generate_app, generate_metadata, build_and_upload_to_supabase

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


def generate_app_background(user_request: str):
    """Background task to generate app"""
    try:
        res = generate_app(user_request)
        metadata = generate_metadata(user_request)
        build_and_upload_to_supabase(res, metadata)
        print(f"App generated successfully for request: {user_request}")
    except Exception as e:
        print(f"Error generating app: {e}")


@app.post("/generate-app")
async def create_app(user_request: str, background_tasks: BackgroundTasks) -> dict:
    background_tasks.add_task(generate_app_background, user_request)
    return {"message": "App generation started in background"}
