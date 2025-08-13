# microcred/app/services/storage_services.py
from __future__ import annotations
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import current_app
from PIL import Image

ALLOWED_EXTS = {"png", "jpg", "jpeg", "webp"}
MAX_SIZE = (256, 256)  # resize bounding box

def ensure_awards_dir() -> Path:
    # static/awards under the app's static folder
    awards_dir = Path(current_app.static_folder) / "awards"
    awards_dir.mkdir(parents=True, exist_ok=True)
    return awards_dir

def award_img_url(file_name: str | None) -> str:
    base = current_app.config.get("AWARD_IMAGE_BASE", "/static/awards")
    return f"{base}/{file_name}" if file_name else f"{base}/default.png"


def save_award_icon(file_storage, slug: str, *, max_size: tuple[int, int] = MAX_SIZE) -> str:
    """
    Resizes and saves the uploaded icon as a PNG named <slug>.png into static/awards.
    Returns the filename to store in the DB.
    """
    ext = (file_storage.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTS:
        ext = "png"  # we’ll re-encode anyway

    # Normalised target filename
    filename = secure_filename(f"{slug}.png")

    awards_dir = ensure_awards_dir()
    dest = awards_dir / filename

    img = Image.open(file_storage.stream).convert("RGBA")
    img.thumbnail(max_size, Image.LANCZOS)
    img.save(dest, format="PNG", optimize=True)
    return filename


def delete_award_icon(filename: str | None) -> None:
    if not filename:
        return
    p = ensure_awards_dir() / filename
    try:
        if p.exists():
            p.unlink()
    except Exception:
        # keep quiet; not fatal
        pass

def rename_icon_if_slug_changed(old_filename: str | None, old_slug: str, new_slug: str) -> str | None:
    """
    If filenames follow '<slug>.png' and slug has changed, rename the file.
    Returns the new filename, or the old one if nothing changed.
    """
    if not old_filename:
        return None
    if old_slug == new_slug:
        return old_filename

    old = ensure_awards_dir() / old_filename
    new_name = secure_filename(f"{new_slug}.png")
    new = ensure_awards_dir() / new_name
    try:
        if old.exists():
            if new.exists():
                new.unlink()
            old.rename(new)
            return new_name
    except Exception:
        # If rename fails, keep the old filename
        return old_filename
    return old_filename
