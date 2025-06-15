import os
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any
import uuid
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import httpx
import aiofiles

app = FastAPI(title="Expo Bundle Upload Service", version="1.0.0")

# Configuration
SUPABASE_URL = "https://ggaiooipedyygqexifzb.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdnYWlvb2lwZWR5eWdxZXhpZnpiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk5MjMwMzMsImV4cCI6MjA2NTQ5OTAzM30.mFmR_NU1ir1d48fkPGvynQ5eNPb6rL88KnlOjH-g1Nw"
UPLOAD_ENDPOINT = f"{SUPABASE_URL}/functions/v1/upload-zip-file"


class BuildUploadService:
    def __init__(self):
        self.mime_types = {
            ".html": "text/html",
            ".js": "application/javascript",
            ".css": "text/css",
            ".json": "application/json",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".svg": "image/svg+xml",
            ".woff": "font/woff",
            ".woff2": "font/woff2",
            ".ttf": "font/ttf",
            ".map": "application/json",
        }

    async def get_all_files(self, dir_path: Path) -> List[Path]:
        """Recursively get all files from directory"""
        all_files = []

        def _get_files_recursive(path: Path):
            for item in path.iterdir():
                if item.is_file():
                    all_files.append(item)
                elif item.is_dir():
                    _get_files_recursive(item)

        _get_files_recursive(dir_path)
        return all_files

    async def run_expo_export(self, template_app_dir: Path) -> None:
        """Run expo export command"""
        print("📦 Building Expo app...")

        if not template_app_dir.exists():
            raise HTTPException(
                status_code=404, detail="template-app directory not found!"
            )

        try:
            print("   Running: CI=1 npx expo export")

            # Set environment variables
            env = os.environ.copy()
            env["CI"] = "1"

            # Run the command
            process = await asyncio.create_subprocess_exec(
                "npx",
                "expo",
                "export",
                cwd=template_app_dir,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Expo export failed"
                raise HTTPException(
                    status_code=500, detail=f"Expo export failed: {error_msg}"
                )

            print("✅ Expo export completed successfully")

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to run expo export: {str(e)}"
            )

    async def upload_single_file(
        self, file_path: Path, relative_path: str, deployment_id: str
    ) -> Dict[str, Any]:
        """Upload a single file to Supabase"""

        async with aiofiles.open(file_path, "rb") as f:
            file_content = await f.read()

        file_name = file_path.name
        file_ext = file_path.suffix
        content_type = self.mime_types.get(file_ext, "application/octet-stream")

        # Prepare form data
        files = {"file": (file_name, file_content, content_type)}

        data = {
            "name": "Expo App File",
            "platform": "ios",
            "deploymentId": deployment_id,
            "relativePath": relative_path,
        }

        headers = {"Authorization": f"Bearer {SUPABASE_ANON_KEY}"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                UPLOAD_ENDPOINT, files=files, data=data, headers=headers, timeout=30.0
            )

        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get("error", "Upload failed")
            raise HTTPException(status_code=response.status_code, detail=error_msg)

        return response.json()

    async def upload_manifest(
        self, manifest: Dict[str, Any], deployment_id: str
    ) -> Dict[str, Any]:
        """Upload deployment manifest"""

        manifest_content = json.dumps(manifest, indent=2).encode("utf-8")

        files = {"file": ("manifest.json", manifest_content, "application/json")}

        data = {
            "name": "Deployment Manifest",
            "platform": "ios",
            "deploymentId": deployment_id,
            "isManifest": "true",
        }

        headers = {"Authorization": f"Bearer {SUPABASE_ANON_KEY}"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                UPLOAD_ENDPOINT, files=files, data=data, headers=headers, timeout=30.0
            )

        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get("error", "Manifest upload failed")
            raise HTTPException(status_code=response.status_code, detail=error_msg)

        return response.json()

    async def build_and_upload(self) -> Dict[str, Any]:
        """Main function to build and upload Expo app"""
        try:
            print("🚀 Starting build and upload process...")

            # Step 1: Navigate to template-app directory and run expo export
            current_dir = Path(__file__).parent
            template_app_dir = current_dir / "template-app"
            template_app_dir = template_app_dir.resolve()

            await self.run_expo_export(template_app_dir)

            # Step 2: Check if dist folder exists
            dist_dir = template_app_dir / "dist"
            if not dist_dir.exists():
                raise HTTPException(
                    status_code=404, detail="dist folder not found after expo export!"
                )

            print("📁 Found dist folder, scanning files...")

            # Step 3: Get all files from dist directory recursively
            all_files = await self.get_all_files(dist_dir)
            print(f"📊 Found {len(all_files)} files to upload")

            # Step 4: Upload each file individually with organized structure
            print("☁️ Starting individual file uploads...")
            upload_results = []
            deployment_id = str(uuid.uuid4())  # Group all files under one deployment

            print(f"🆔 Deployment ID: {deployment_id}")
            print(f"📂 Files will be organized in: deployments/{deployment_id}/")

            for i, file_path in enumerate(all_files):
                relative_path = str(file_path.relative_to(dist_dir))

                print(f"📤 Uploading {i + 1}/{len(all_files)}: {relative_path}")

                try:
                    result = await self.upload_single_file(
                        file_path, relative_path, deployment_id
                    )

                    upload_results.append(
                        {
                            "originalPath": relative_path,
                            "fileId": result.get("fileId"),
                            "fileName": result.get("fileName"),
                            "publicUrl": result.get("publicUrl"),
                            "uploadPath": result.get("uploadPath"),
                            "fileSize": result.get("fileSize"),
                            "fileType": result.get("fileType"),
                        }
                    )

                    print(f"   ✅ Success: {result.get('uploadPath')}")

                except Exception as error:
                    print(f"   ❌ Failed: {relative_path} - {str(error)}")

            # Step 5: Create and upload manifest file
            print("📋 Creating deployment manifest...")

            # Find entry point (index.html or first file)
            entry_point = None
            for file_result in upload_results:
                if "index.html" in file_result["originalPath"]:
                    entry_point = file_result
                    break

            if not entry_point and upload_results:
                entry_point = upload_results[0]

            manifest = {
                "deploymentId": deployment_id,
                "platform": "ios",
                "timestamp": datetime.utcnow().isoformat(),
                "totalFiles": len(upload_results),
                "files": upload_results,
                "entryPoint": entry_point,
                "baseUrl": f"{SUPABASE_URL}/storage/v1/object/public/apps/deployments/{deployment_id}/",
            }

            manifest_result = await self.upload_manifest(manifest, deployment_id)

            print("🎉 Upload completed successfully!")
            print(f"📄 Deployment ID: {deployment_id}")
            print(f"📂 Deployment Folder: deployments/{deployment_id}/")
            print(f"📋 Manifest URL: {manifest_result.get('publicUrl')}")
            print(f"📊 Total files uploaded: {len(upload_results)}")
            print(f"🌐 Base URL: {manifest['baseUrl']}")

            # Return the manifest for database storage
            return {
                "deploymentId": deployment_id,
                "manifestUrl": manifest_result.get("publicUrl"),
                "baseUrl": manifest["baseUrl"],
                "totalFiles": len(upload_results),
                "files": upload_results,
            }

        except HTTPException:
            raise
        except Exception as error:
            print(f"❌ Error: {str(error)}")
            raise HTTPException(status_code=500, detail=str(error))


# Initialize service
build_service = BuildUploadService()


@app.post("/build-and-upload")
async def build_and_upload_endpoint():
    """
    Build and upload Expo app endpoint

    This endpoint:
    1. Runs expo export on the template-app directory
    2. Uploads all generated files to Supabase
    3. Creates and uploads a deployment manifest
    4. Returns deployment information
    """
    try:
        result = await build_service.build_and_upload()
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Build and upload completed successfully",
                "data": result,
            },
        )
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code, content={"success": False, "error": e.detail}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Expo Bundle Upload Service is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
