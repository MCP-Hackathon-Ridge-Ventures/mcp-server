#!/usr/bin/env python3
"""
Standalone Python script to build and upload Expo apps to Supabase
This is a direct Python equivalent of the original JavaScript script
"""

import os
import json
import asyncio
import shutil
import tempfile
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

import httpx
import aiofiles

# Configuration
SUPABASE_URL = "https://ggaiooipedyygqexifzb.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdnYWlvb2lwZWR5eWdxZXhpZnpiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk5MjMwMzMsImV4cCI6MjA2NTQ5OTAzM30.mFmR_NU1ir1d48fkPGvynQ5eNPb6rL88KnlOjH-g1Nw"
UPLOAD_ENDPOINT = f"{SUPABASE_URL}/functions/v1/upload-zip-file"

# MIME type mapping
MIME_TYPES = {
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
    template_app_dir: Path, index_jsx_content: str
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


async def cleanup_temp_directory(temp_dir: Path) -> None:
    """Clean up temporary directory"""
    try:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"🧹 Cleaned up temporary directory: {temp_dir}")
    except Exception as e:
        print(f"⚠️ Warning: Failed to clean up temporary directory: {e}")


def get_all_files(dir_path: Path) -> List[Path]:
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


async def run_expo_export(template_app_dir: Path) -> None:
    """Run expo export command"""
    print("📦 Building Expo app...")

    if not template_app_dir.exists():
        raise FileNotFoundError("template-app directory not found!")

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

        print("   Running: CI=1 npx expo export --platform ios")

        # Set environment variables
        env = os.environ.copy()
        env["CI"] = "1"

        # Run the command
        process = await asyncio.create_subprocess_exec(
            "npx",
            "expo",
            "export",
            "--platform",
            "ios",
            cwd=template_app_dir,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Expo export failed"
            raise RuntimeError(f"Expo export failed: {error_msg}")

        print("✅ Expo export completed successfully")

    except Exception as e:
        raise RuntimeError(f"Failed to run expo export: {str(e)}")


async def upload_single_file(
    file_path: Path, relative_path: str, deployment_id: str
) -> Dict[str, Any]:
    """Upload a single file to Supabase"""

    async with aiofiles.open(file_path, "rb") as f:
        file_content = await f.read()

    file_name = file_path.name
    file_ext = file_path.suffix
    content_type = MIME_TYPES.get(file_ext, "application/octet-stream")

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
        raise RuntimeError(f"Upload failed: {error_msg}")

    return response.json()


async def upload_manifest(
    manifest: Dict[str, Any], deployment_id: str
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
        raise RuntimeError(f"Manifest upload failed: {error_msg}")

    return response.json()


async def build_and_upload(index_jsx_content: Optional[str] = None) -> Dict[str, Any]:
    """Main function to build and upload Expo app"""
    temp_app_dir = None
    try:
        print("🚀 Starting build and upload process...")

        # Step 1: Set up the build directory
        current_dir = Path(__file__).parent
        template_app_dir = current_dir / "template-app"
        template_app_dir = template_app_dir.resolve()

        if index_jsx_content:
            # Copy template-app + custom index.jsx to temporary directory
            temp_app_dir = await copy_template_with_custom_index(
                template_app_dir, index_jsx_content
            )
            build_dir = temp_app_dir
        else:
            # Use original template-app directory
            build_dir = template_app_dir

        await run_expo_export(build_dir)

        # Step 2: Check if dist folder exists
        dist_dir = build_dir / "dist"
        if not dist_dir.exists():
            raise FileNotFoundError("dist folder not found after expo export!")

        print("📁 Found dist folder, scanning files...")

        # Step 3: Get all files from dist directory recursively
        all_files = get_all_files(dist_dir)
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
                result = await upload_single_file(
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

        manifest_result = await upload_manifest(manifest, deployment_id)

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

    except Exception as error:
        print(f"❌ Error: {str(error)}")
        raise
    finally:
        # Clean up temporary directory if it was created
        if temp_app_dir:
            await cleanup_temp_directory(temp_app_dir.parent)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Build and upload Expo app to Supabase"
    )
    parser.add_argument(
        "--index-jsx", type=str, help="Path to custom index.jsx file to use as App.js"
    )

    args = parser.parse_args()

    try:
        index_jsx_content = None

        if args.index_jsx:
            index_jsx_path = Path(args.index_jsx)
            if not index_jsx_path.exists():
                raise FileNotFoundError(f"Index.jsx file not found: {index_jsx_path}")

            async with aiofiles.open(index_jsx_path, "r") as f:
                index_jsx_content = await f.read()

            print(f"📄 Using custom index.jsx file: {index_jsx_path}")

        result = await build_and_upload(index_jsx_content)
        print("\n🎯 Final Result:")
        print(json.dumps(result, indent=2))
    except Exception as error:
        print(f"💥 Final Error: {str(error)}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
