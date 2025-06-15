import json
import os
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.supabase import supabase


class BuildService:
    def __init__(self):
        self.mime_types = {
            ".html": "text/html",
            ".js": "application/javascript",
            ".ts": "application/javascript",
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

    def copy_template_with_custom_index(
        self, template_app_dir: Path, app_jsx_content: str
    ) -> Path:
        """Copy template-app to a temporary directory and replace index.jsx"""
        # Create a temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix="expo_build_"))
        temp_app_dir = temp_dir / "app"

        print(f"📋 Creating temporary build directory: {temp_app_dir}")

        try:
            # Copy the entire template-app directory
            shutil.copytree(template_app_dir, temp_app_dir)
            print("📁 Template app copied successfully")

            # Write the custom index.jsx content as App.jsx
            app_file_path = temp_app_dir / "src" / "App.jsx"
            with open(app_file_path, "w") as f:
                f.write(app_jsx_content)

            print(f"✅ Custom App.jsx written to: {app_file_path}")

            return temp_app_dir

        except Exception as e:
            # Clean up on error
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise e

    def cleanup_temp_directory(self, temp_dir: Path) -> None:
        """Clean up temporary directory"""
        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
                print(f"🧹 Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            print(f"⚠️ Warning: Failed to clean up temporary directory: {e}")

    def get_all_files(self, dir_path: Path) -> List[Path]:
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

    def run_html_export(self, template_app_dir: Path) -> None:
        """Run npm build command"""
        print("📦 Building HTML app...")

        if not template_app_dir.exists():
            raise FileNotFoundError("template-app directory not found!")

        try:
            # First run npm install to ensure dependencies are installed
            print("   Running: npm install")
            install_result = subprocess.run(
                ["npm", "install"], cwd=template_app_dir, capture_output=True, text=True
            )

            if install_result.returncode != 0:
                error_msg = (
                    install_result.stderr
                    if install_result.stderr
                    else "npm install failed"
                )
                print(f"   ⚠️ npm install warning: {error_msg}")
            else:
                print("   ✅ npm install completed")

            print("   Running: npm run build")

            # Set environment variables
            env = os.environ.copy()
            env["CI"] = "1"

            # Run the build command
            build_result = subprocess.run(
                ["npm", "run", "build"],
                cwd=template_app_dir,
                env=env,
                capture_output=True,
                text=True,
            )

            if build_result.returncode != 0:
                error_msg = (
                    build_result.stderr if build_result.stderr else "Build failed"
                )
                raise RuntimeError(f"Build failed: {error_msg}")

            print("✅ Build completed successfully")

        except Exception as e:
            raise RuntimeError(f"Failed to run build: {str(e)}")

    def build_app(
        self, app_jsx_content: Optional[str] = None, output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Main function to build the app locally"""
        temp_app_dir = None
        try:
            print("🚀 Starting build process...")

            # Step 1: Set up the build directory
            current_dir = Path(__file__).parent
            template_app_dir = current_dir.parent.parent / "template-web-app"
            template_app_dir = template_app_dir.resolve()

            if app_jsx_content:
                # Copy template-app + custom index.jsx to temporary directory
                temp_app_dir = self.copy_template_with_custom_index(
                    template_app_dir, app_jsx_content
                )
                build_dir = temp_app_dir
            else:
                # Use original template-app directory
                build_dir = template_app_dir

            self.run_html_export(build_dir)

            # Step 2: Check if dist folder exists
            dist_dir = build_dir / "web"
            if not dist_dir.exists():
                raise FileNotFoundError("web folder not found after build!")

            print("📁 Found web folder, scanning files...")

            # Step 3: Get all files from dist directory recursively
            all_files = self.get_all_files(dist_dir)
            print(f"📊 Found {len(all_files)} files in web output")

            # Step 4: Optionally copy files to output directory
            if output_dir:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)

                print(f"📂 Copying build output to: {output_dir}")

                # Copy entire dist directory to output directory
                if output_dir.exists():
                    shutil.rmtree(output_dir, ignore_errors=True)
                shutil.copytree(dist_dir, output_dir)

                print(f"✅ Build output copied to: {output_dir}")

            build_id = str(uuid.uuid4())

            # Upload files to supabase storage
            for file in all_files:
                supabase.storage.from_("apps").upload(
                    file=file,
                    path=f"deployments/{build_id}/{file.name}",
                )

            return {
                "success": True,
                "message": "Build completed successfully",
                "buildId": build_id,
                "distDir": str(dist_dir),
                "outputDir": str(output_dir) if output_dir else None,
                "fileCount": len(all_files),
                "files": [str(f.relative_to(dist_dir)) for f in all_files],
            }

        except Exception as error:
            print(f"❌ Error: {str(error)}")
            raise RuntimeError(str(error))
        finally:
            # Clean up temporary directory if it was created
            if temp_app_dir:
                self.cleanup_temp_directory(temp_app_dir.parent)


def build_app_local(
    app_jsx_content: Optional[str] = None, output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build app locally without any API calls

    Args:
        app_jsx_content: Optional custom JSX content for App.jsx
        output_dir: Optional directory to copy the build output to

    Returns:
        Dictionary with build results and information
    """
    build_service = BuildService()
    output_path = Path(output_dir) if output_dir else None
    return build_service.build_app(app_jsx_content, output_path)


def build_app_from_file(
    jsx_file_path: str, output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build app from a JSX file

    Args:
        jsx_file_path: Path to the JSX file to use as App.jsx
        output_dir: Optional directory to copy the build output to

    Returns:
        Dictionary with build results and information
    """
    jsx_path = Path(jsx_file_path)
    if not jsx_path.exists():
        raise FileNotFoundError(f"JSX file not found: {jsx_file_path}")

    if not jsx_path.suffix.lower() in [".jsx", ".js"]:
        raise ValueError("File must be a .jsx or .js file")

    with open(jsx_path, "r", encoding="utf-8") as f:
        jsx_content = f.read()

    return build_app_local(jsx_content, output_dir)


if __name__ == "__main__":
    # Example usage
    try:
        # Build with default template
        result = build_app_local(output_dir="./build_output")
        print(f"Build successful: {result}")

        # Or build with custom JSX content
        # custom_jsx = """
        # import React from 'react';
        #
        # export default function App() {
        #   return (
        #     <div>
        #       <h1>Hello World!</h1>
        #       <p>This is a custom app.</p>
        #     </div>
        #   );
        # }
        # """
        # result = build_app_local(custom_jsx, "./custom_build")
        # print(f"Custom build successful: {result}")

    except Exception as e:
        print(f"Build failed: {e}")
