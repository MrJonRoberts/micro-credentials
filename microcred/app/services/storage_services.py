from pathlib import Path
from flask import current_app

class StorageService:
    def award_image_url(self, filename: str | None) -> str | None:
        if not filename:
            return None
        base = current_app.config.get("AWARD_IMAGE_BASE", "/static/awards").rstrip("/")
        return f"{base}/{filename}"

    def ensure_awards_dir(self) -> Path:
        root = Path(current_app.root_path) / "static" / "awards"
        root.mkdir(parents=True, exist_ok=True)
        return root
