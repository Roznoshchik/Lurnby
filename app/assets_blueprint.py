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
        """Get CSS files for an entry point"""
        if not is_production:
            return []
        try:
            css_files = manifest.get(file_path, {}).get('css', [])
            return [f"/static/dist/{css_file}" for css_file in css_files]
        except Exception:
            return []

    return {
        "asset": prod_asset if is_production else dev_asset,
        "asset_css": asset_css,
        "is_production": is_production,
    }
