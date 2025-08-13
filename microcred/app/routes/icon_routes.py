# app/routes/icon_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, send_from_directory, current_app
import os
from flask_login import login_required
from ._utils import roles_required
from microcred.app.extensions import db
from microcred.app.models.icons import Icon
from microcred.app.models.award import Award
from microcred.app.services.icon_service import (
    save_icon_file, create_icon, update_icon, delete_icon,
    get_icon_by_id, get_icon_by_name, icons_root
)

from math import ceil
from werkzeug.utils import secure_filename
from sqlalchemy import func
from PIL import Image
import os
import re

ALLOWED_EXT = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg'}  # SVG passes through unmodified

icons_bp = Blueprint("icons", __name__, url_prefix="/icons")

# --- Config helpers ---------------------------------------------------------

def icons_fs_root() -> str:
    """Absolute filesystem path to Icons directory."""
    # app.root_path == microcred/app
    return os.path.join(current_app.root_path, 'static', 'Icons')

def icons_url_base() -> str:
    """URL base used in templates."""
    return '/static/Icons'


# ---------- CRUD UI ----------

@icons_bp.route("/", methods=["GET"])
@login_required
def index():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    # Pagination inputs (with sensible bounds)
    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1
    try:
        per_page = int(request.args.get("per_page", 24))  # default 24/thumb grid friendly
    except ValueError:
        per_page = 24
    per_page = min(max(per_page, 6), 96)  # clamp 6–96

    query = Icon.query
    if q:
        query = query.filter(Icon.name.ilike(f"%{q}%"))
    if category:
        query = query.filter(Icon.category == category)

    query = query.order_by(Icon.category.asc(), Icon.name.asc())

    # Works on Flask‑SQLAlchemy 2.x
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    icons = pagination.items



    categories = db.session.query(Icon.category).distinct().all()
    categories = [c[0] for c in categories]
    start_page = max(1, pagination.page - 2)
    end_page = min(pagination.pages, pagination.page + 2)
    return render_template(
        "icons/index.html",
        icons=icons,
        categories=categories,
        q=q,
        category=category,
        pagination=pagination,
        per_page=per_page,
        start_page=start_page,
        end_page=end_page
    )


@icons_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        category = (request.form.get("category") or "").strip()
        file = request.files.get("file")
        chosen_from_picker = (request.form.get("icon_filename") or "").strip()

        # Basic validation
        if not name or not category:
            flash("Name and category are required.", "danger")
            return redirect(url_for("icons.create"))

        if (not file or not getattr(file, "filename", "")) and not chosen_from_picker:
            flash("Upload a file or choose an icon from the library.", "danger")
            return redirect(url_for("icons.create"))

        try:
            if file and getattr(file, "filename", ""):
                # Save uploaded file into /static/Icons/<category>/...
                url = save_icon_file_picker(file, category)
            else:
                # Use picker value (absolute or relative); validate and normalise
                url = normalise_picker_value(chosen_from_picker)
                if not url:
                    flash("Invalid icon selected.", "danger")
                    return redirect(url_for("icons.create"))

                # Optional: enforce that picker category matches the field
                # If you want to override category from the URL, uncomment:
                # rel = url[len(icons_url_base()) + 1:]            # 'pack/icon.svg'
                # picked_category = rel.split('/', 1)[0] if '/' in rel else ''
                # category = picked_category or category

            # Create DB row
            icon = Icon(name=name, category=category, url=url)
            db.session.add(icon)
            db.session.commit()

            flash("Icon created.", "success")
            return redirect(url_for("icons.index"))

        except Exception as e:
            current_app.logger.exception(e)
            flash(f"Error creating icon: {e}", "danger")
            return redirect(url_for("icons.create"))

    # GET
    return render_template("icons/form.html", icon=None)
@icons_bp.route("/<int:icon_id>/edit", methods=["GET", "POST"])
@login_required

def edit(icon_id):
    icon = get_icon_by_id(icon_id)
    if not icon:
        abort(404)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        file = request.files.get("file")

        try:
            # If a new file is uploaded, save it and update filename
            if file and file.filename.strip():
                new_filename = save_icon_file(file, category or icon.category)
                icon = update_icon(icon, name=name or icon.name, category=category or icon.category, filename=new_filename)
            else:
                icon = update_icon(icon, name=name or icon.name, category=category or icon.category)
            flash("Icon updated.", "success")
            return redirect(url_for("icons.index"))
        except Exception as e:
            current_app.logger.exception(e)
            flash(f"Error updating icon: {e}", "danger")
            return redirect(url_for("icons.edit", icon_id=icon.id))

    return render_template("icons/form.html", icon=icon)

@icons_bp.route("/<int:icon_id>/delete", methods=["POST"])
@login_required
@roles_required('admin')
def remove(icon_id):
    icon = get_icon_by_id(icon_id)
    if not icon:
        abort(404)
    try:
        # delete_file=True will remove the actual file from disk
        delete_icon(icon, delete_file=bool(request.form.get("delete_file")))
        flash("Icon deleted.", "success")
    except Exception as e:
        current_app.logger.exception(e)
        flash(f"Error deleting icon: {e}", "danger")
    return redirect(url_for("icons.index"))

# ---------- API/Utility endpoints ----------

@icons_bp.route("/api/<int:icon_id>", methods=["GET"])
def api_get_by_id(icon_id):
    icon = get_icon_by_id(icon_id)
    if not icon:
        abort(404)
    return jsonify({"id": icon.id, "name": icon.name, "category": icon.category, "filename": icon.filename, "url": icon.url})

@icons_bp.route("/api/by-name/<string:name>", methods=["GET"])
def api_get_by_name(name):
    icon = get_icon_by_name(name)
    if not icon:
        abort(404)
    return jsonify({"id": icon.id, "name": icon.name, "category": icon.category, "filename": icon.filename, "url": icon.url})

# @icons_bp.route("/api/by-url", methods=["GET"])
# def api_get_by_url():
#     # Expect ?url=/Icons/<category>/<filename>
#     url = request.args.get("url", "").strip()
#     icon = get_icon_by_url(url)
#     if not icon:
#         abort(404)
#     return jsonify({"id": icon.id, "name": icon.name, "category": icon.category, "filename": icon.filename, "url": icon.url})

# ---------- Serve icon by id/name/url (returns the image file) ----------

@icons_bp.route("/image/by-id/<int:icon_id>")
def image_by_id(icon_id):
    icon = get_icon_by_id(icon_id)
    if not icon:
        abort(404)
    return send_from_directory(os.path.join(icons_root(), icon.category), icon.filename)

@icons_bp.route("/image/by-name/<string:name>")
def image_by_name(name):
    icon = get_icon_by_name(name)
    if not icon:
        abort(404)
    return send_from_directory(os.path.join(icons_root(), icon.category), icon.filename)

# @icons_bp.route("/image/by-url")
# def image_by_url():
#     """
#     Accepts ?url=/Icons/<category>/<filename>
#     This is useful if you only know the stored URL.
#     """
#     url = request.args.get("url", "").strip()
#     icon = get_icon_by_url(url)
#     if not icon:
#         abort(404)
#     return send_from_directory(os.path.join(icons_root(), icon.category), icon.filename)

@icons_bp.route('/picker')
def icon_picker():
    """HTML fragment for the popover: a small, clickable grid of icons."""
    page = max(int(request.args.get('page', 1)), 1)
    per_page = min(max(int(request.args.get('per_page', 60)), 12), 120)

    q = Icon.query
    # Optional: filter by category from ?category=... if you like
    category = request.args.get('category')
    if category:
        q = q.filter_by(category=category)

    total = q.count()
    icons = (q.order_by(Icon.name)
               .offset((page - 1) * per_page)
               .limit(per_page)
               .all())

    pages = max(ceil(total / per_page), 1)
    return render_template('admin/_icon_picker_grid.html',
                           icons=icons, page=page, pages=pages,
                           category=category or '')



# --- Utilities --------------------------------------------------------------

_slugify_rx = re.compile(r'[^a-z0-9]+')

def slugify(value: str) -> str:
    s = value.strip().lower()
    s = _slugify_rx.sub('-', s).strip('-')
    return s or 'award'

def unique_slug(base: str, award_id: int | None = None) -> str:
    """Ensure slug is unique. If editing, ignore current record."""
    slug = base
    i = 2
    while True:
        q = Award.query.filter(func.lower(Award.slug) == slug.lower())
        if award_id:
            q = q.filter(Award.id != award_id)
        exists = db.session.query(q.exists()).scalar()
        if not exists:
            return slug
        slug = f"{base}-{i}"
        i += 1

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def save_upload(file_storage, subdir='uploads') -> str:
    """
    Save an uploaded image under static/Icons/<subdir>/<filename>.
    - Returns the relative path under Icons (e.g. 'uploads/my.png').
    - Raster images are resized to max 256x256. SVG is copied as-is.
    """
    filename = secure_filename(file_storage.filename or '')
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ALLOWED_EXT:
        raise ValueError('Unsupported file type.')

    # Ensure subdir exists
    fs_root = icons_fs_root()
    target_dir = os.path.join(fs_root, subdir)
    ensure_dir(target_dir)

    # De-dupe filename if needed
    base_name, _ = os.path.splitext(filename)
    candidate = filename
    i = 2
    while os.path.exists(os.path.join(target_dir, candidate)):
        candidate = f"{base_name}-{i}{ext}"
        i += 1

    fs_path = os.path.join(target_dir, candidate)

    if ext == '.svg':
        # Copy raw
        file_storage.save(fs_path)
    else:
        # Resize raster image to max 256x256, keep aspect
        img = Image.open(file_storage.stream).convert('RGBA' if ext in {'.png', '.webp'} else 'RGB')
        img.thumbnail((256, 256))
        img.save(fs_path)

    # Return path relative to Icons root
    return f"{subdir}/{candidate}"

def normalise_library_icon(url_or_rel: str) -> str | None:
    """
    Accepts '/static/Icons/pack/icon.svg' or 'pack/icon.svg' and
    returns a safe relative path like 'pack/icon.svg' if valid.
    Rejects anything that escapes Icons.
    """
    val = (url_or_rel or '').strip()
    if not val:
        return None
    # Strip leading url base if present
    if val.startswith(icons_url_base() + '/'):
        val = val[len(icons_url_base()) + 1:]

    # Prevent path traversal
    if val.startswith('/') or '..' in val:
        return None

    # Must exist under Icons
    if not os.path.exists(os.path.join(icons_fs_root(), val)):
        # We can still allow it if you don’t require existence, but safer to check.
        return None

    # Check extension
    ext = os.path.splitext(val)[1].lower()
    if ext not in ALLOWED_EXT:
        return None

    return val

def icons_fs_root() -> str:
    # e.g. <project>/microcred/app/static/Icons
    return os.path.join(current_app.root_path, 'static', 'Icons')

def icons_url_base() -> str:
    return '/static/Icons'

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def save_icon_file_picker(file_storage, category: str) -> str:
    """
    Save uploaded file to static/Icons/<category>/<filename>.
    Returns the final served URL: /static/Icons/<category>/<filename>
    """
    if not file_storage or not getattr(file_storage, 'filename', ''):
        raise ValueError('No file supplied.')

    filename = secure_filename(file_storage.filename)
    if not filename:
        raise ValueError('Invalid filename.')

    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXT:
        raise ValueError('Unsupported file type.')

    # ensure category dir
    fs_root = icons_fs_root()
    target_dir = os.path.join(fs_root, category)
    ensure_dir(target_dir)

    # de-dupe filename
    name_only, _ = os.path.splitext(filename)
    candidate = filename
    i = 2
    while os.path.exists(os.path.join(target_dir, candidate)):
        candidate = f"{name_only}-{i}{ext}"
        i += 1

    # save
    fs_path = os.path.join(target_dir, candidate)
    file_storage.save(fs_path)

    # return URL used by templates
    return f"{icons_url_base()}/{category}/{candidate}"

def normalise_picker_value(val: str) -> str | None:
    """
    Accepts '/static/Icons/pack/icon.svg' or 'pack/icon.svg'.
    Returns a safe absolute URL '/static/Icons/...', or None if invalid.
    """
    if not val:
        return None
    val = val.strip()

    # If relative (e.g. 'pack/icon.svg'), make absolute
    if not val.startswith(icons_url_base()):
        if val.startswith('/'):
            # user tried '/something' that isn't under Icons
            return None
        val = f"{icons_url_base()}/{val}"

    # Validate it points under Icons and exists on disk
    if not val.startswith(icons_url_base() + '/'):
        return None

    rel = val[len(icons_url_base()) + 1:]  # e.g. 'pack/icon.svg'
    if '..' in rel or rel.startswith('/'):
        return None

    ext = os.path.splitext(rel)[1].lower()
    if ext not in ALLOWED_EXT:
        return None

    fs_path = os.path.join(icons_fs_root(), rel)
    if not os.path.exists(fs_path):
        # If you want to allow referencing an icon that isn't on disk yet,
        # remove this existence check. Safer to keep it.
        return None

    return val