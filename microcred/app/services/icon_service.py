# app/services/icon_service.py
import os
from werkzeug.utils import secure_filename
from flask import current_app
from microcred.app.extensions import db
from microcred.app.models.icons import Icon

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def icons_root() -> str:
    # Physical path to /static/Icons
    return os.path.join(current_app.root_path, "static", "Icons")

def save_icon_file(upload_file, category: str) -> str:
    """
    Saves the uploaded file into /static/Icons/<category>/<filename>.
    Returns the stored filename.
    """
    if upload_file is None or upload_file.filename.strip() == "":
        raise ValueError("No file provided.")
    if not allowed_file(upload_file.filename):
        raise ValueError("File type not allowed.")

    safe_name = secure_filename(upload_file.filename)
    cat_dir = os.path.join(icons_root(), category)
    os.makedirs(cat_dir, exist_ok=True)

    target_path = os.path.join(cat_dir, safe_name)
    # if filename exists, uniquify
    if os.path.exists(target_path):
        name, ext = os.path.splitext(safe_name)
        i = 1
        while True:
            candidate = f"{name}_{i}{ext}"
            if not os.path.exists(os.path.join(cat_dir, candidate)):
                safe_name = candidate
                target_path = os.path.join(cat_dir, candidate)
                break
            i += 1

    upload_file.save(target_path)
    return safe_name

def create_icon(name: str, category: str, filename: str) -> Icon:
    icon = Icon(name=name.strip(), category=category.strip(), filename=filename.strip()) #,
                # url=f"/static/Icons/{category}/{filename}")
    db.session.add(icon)
    db.session.commit()
    return icon

def update_icon(icon: Icon, name: str | None = None, category: str | None = None, filename: str | None = None) -> Icon:
    if name is not None:
        icon.name = name.strip()
    if category is not None:
        icon.category = category.strip()
    if filename is not None:
        icon.filename = filename.strip()
    # icon.url = icon.compute_url()
    db.session.commit()
    return icon

def delete_icon(icon: Icon, delete_file: bool = False) -> None:
    if delete_file:
        try:
            path = os.path.join(icons_root(), icon.category, icon.filename)
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            # Swallow file errors; the DB delete still proceeds
            pass
    db.session.delete(icon)
    db.session.commit()

def get_icon_by_id(icon_id: int) -> Icon | None:
    return Icon.query.get(icon_id)

def get_icon_by_name(name: str) -> Icon | None:
    return Icon.query.filter(Icon.name == name).first()

#def get_icon_by_url(url: str) -> Icon | None:
  # normalise: stored url looks like /Icons/<category>/<filename>
  #  return Icon.query.filter(Icon.url == url).first()
