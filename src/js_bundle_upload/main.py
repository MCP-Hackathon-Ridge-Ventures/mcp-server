import os
import json
import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File
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
            ".jsx": "application/javascript",
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

    async def copy_template_with_custom_index(
        self, template_app_dir: Path, index_jsx_content: str
    ) -> Path:
        """Copy template-app to a temporary directory and replace index.jsx"""
        # Create a temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix="expo_build_"))
        temp_app_dir = temp_dir / "app"

        print(f"📋 Creating temporary build directory: {temp_app_dir}")

        try:
            # Copy the entire template-app directory
            if template_app_dir.exists():
                shutil.copytree(template_app_dir, temp_app_dir)
                print("📁 Template app copied successfully")
            else:
                # Create a basic template structure if template-app doesn't exist
                print("⚠️ Template app not found, creating basic structure")
                temp_app_dir.mkdir(parents=True, exist_ok=True)

                # Create basic package.json
                package_json = {
                    "name": "expo-custom-app",
                    "version": "1.0.0",
                    "main": "index.js",
                    "scripts": {"start": "expo start", "build": "expo export"},
                    "dependencies": {
                        "expo": "~50.0.0",
                        "react": "18.2.0",
                        "react-native": "0.73.0",
                    },
                }

                async with aiofiles.open(temp_app_dir / "package.json", "w") as f:
                    await f.write(json.dumps(package_json, indent=2))

                # Create basic app.json
                app_json = {
                    "expo": {
                        "name": "Custom Expo App",
                        "slug": "custom-expo-app",
                        "version": "1.0.0",
                        "platforms": ["ios", "android", "web"],
                    }
                }

                async with aiofiles.open(temp_app_dir / "app.json", "w") as f:
                    await f.write(json.dumps(app_json, indent=2))

                # Create basic index.js entry point
                index_js_content = """import { registerRootComponent } from 'expo';
import App from './App';

registerRootComponent(App);
"""
                async with aiofiles.open(temp_app_dir / "index.js", "w") as f:
                    await f.write(index_js_content)

            # Write the custom index.jsx content as App.js (or App.jsx)
            app_file_path = temp_app_dir / "App.js"
            async with aiofiles.open(app_file_path, "w") as f:
                await f.write(index_jsx_content)

            print(f"✅ Custom App.js written to: {app_file_path}")

            return temp_app_dir

        except Exception as e:
            # Clean up on error
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise e

    async def cleanup_temp_directory(self, temp_dir: Path) -> None:
        """Clean up temporary directory"""
        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
                print(f"🧹 Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            print(f"⚠️ Warning: Failed to clean up temporary directory: {e}")

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
            # First run npm install to ensure dependencies are installed
            print("   Running: npm install")
            install_process = await asyncio.create_subprocess_exec(
                "npm",
                "install",
                cwd=template_app_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            install_stdout, install_stderr = await install_process.communicate()

            if install_process.returncode != 0:
                error_msg = (
                    install_stderr.decode() if install_stderr else "npm install failed"
                )
                print(f"   ⚠️ npm install warning: {error_msg}")
            else:
                print("   ✅ npm install completed")

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

    async def build_and_upload(
        self, index_jsx_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Main function to build and upload Expo app"""
        temp_app_dir = None
        try:
            print("🚀 Starting build and upload process...")

            # Step 1: Set up the build directory
            current_dir = Path(__file__).parent
            template_app_dir = current_dir.parent.parent / "template-app"
            template_app_dir = template_app_dir.resolve()

            if index_jsx_content:
                # Copy template-app + custom index.jsx to temporary directory
                temp_app_dir = await self.copy_template_with_custom_index(
                    template_app_dir, index_jsx_content
                )
                build_dir = temp_app_dir
            else:
                # Use original template-app directory
                build_dir = template_app_dir

            await self.run_expo_export(build_dir)

            # Step 2: Check if dist folder exists
            dist_dir = build_dir / "dist"
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
        finally:
            # Clean up temporary directory if it was created
            if temp_app_dir:
                await self.cleanup_temp_directory(temp_app_dir.parent)


# Initialize service
build_service = BuildUploadService()


@app.post("/build-and-upload")
async def build_and_upload_endpoint(index_jsx: UploadFile = File(None)):
    """
    Build and upload Expo app endpoint

    This endpoint:
    1. Optionally accepts an index.jsx file to customize the app
    2. Copies template-app + custom index.jsx to a temporary directory (if provided)
    3. Runs expo export on the build directory
    4. Uploads all generated files to Supabase
    5. Creates and uploads a deployment manifest
    6. Returns deployment information
    """
    try:
        index_jsx_content = None

        if index_jsx:
            # Validate file type
            if not index_jsx.filename.endswith((".jsx", ".js")):
                raise HTTPException(
                    status_code=400, detail="File must be a .jsx or .js file"
                )

            # Read the uploaded file content
            content = await index_jsx.read()
            index_jsx_content = content.decode("utf-8")
            print(f"📄 Received custom index.jsx file: {index_jsx.filename}")

        result = await build_service.build_and_upload(index_jsx_content)
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
