import os
import tempfile

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from supabase import Client, create_client

load_dotenv()

supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

engine = create_engine(os.getenv("POSTGRES_URL"))
Session = sessionmaker(bind=engine)
session = Session()


def download_from_bucket(file_path: str) -> str:
    try:
        temp_file = None
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            response = supabase.storage.from_("apps").download(file_path)
            temp_file.write(response)
            temp_file.seek(0)
            with open(temp_file.name, "r") as f:
                content = f.read()
            return content
        finally:
            if temp_file:
                temp_file.close()
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
    except Exception as e:
        print(f"Error downloading file: {e}")
        return ""
