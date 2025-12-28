import json
import os
from pathlib import Path

from flask import Blueprint

FLASK_DEBUG = os.getenv("FLASK_DEBUG", "0")
VITE_ORIGIN = os.getenv("VITE_ORIGIN", "http://localhost:5173")

is_production = FLASK_DEBUG != "1"
project_path = Path(os.path.dirname(os.path.abspath(__file__)))

assets_blueprint = Blueprint(
    "assets_blueprint",
    __name__,
    static_folder="static/dist/bundled",
    static_url_path="/static/dist/bundled",
)

manifest = {}
if is_production:
    manifest_path = project_path / "static/dist/manifest.json"
    try:
        with open(manifest_path, "r") as content:
            manifest = json.load(content)
    except OSError as exception:
        raise OSError(
            f"Manifest file not found at {manifest_path}. Run `npm run build`."
        ) from exception


@assets_blueprint.app_context_processor
def add_context():
    def dev_asset(file_path):
        return f"{VITE_ORIGIN}/static/dist/{file_path}"

    def prod_asset(file_path):
        try:
            return f"/static/dist/{manifest[file_path]['file']}"
        except Exception:
            return "asset-not-found"

    def asset_css(file_path):
        """Get CSS files for an entry point and all its imports"""
        if not is_production:
            return []

        def collect_css(entry_key, visited=None):
            """Recursively collect CSS from an entry and its imports"""
            if visited is None:
                visited = set()

            if entry_key in visited:
                return []

            visited.add(entry_key)
            css_files = []

            try:
                entry = manifest.get(entry_key, {})

                # Collect direct CSS files
                css_files.extend(entry.get('css', []))

                # Recursively collect CSS from imports
                for import_key in entry.get('imports', []):
                    css_files.extend(collect_css(import_key, visited))

            except Exception:
                pass

            return css_files

        try:
            css_files = collect_css(file_path)
            return [f"/static/dist/{css_file}" for css_file in css_files]
        except Exception:
            return []

    return {
        "asset": prod_asset if is_production else dev_asset,
        "asset_css": asset_css,
        "is_production": is_production,
    }
