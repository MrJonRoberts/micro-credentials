# bootstrap_modern.py
import sqlite3
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.resolve()
PKG = ROOT / "microcred" / "app"
INSTANCE = ROOT / "microcred" / "instance"
DB_PATH = INSTANCE / "app.db"

DIRS = [
    "microcred",
    "microcred/app",
    "microcred/app/routes",
    "microcred/app/views",
    "microcred/app/models",
    "microcred/app/services",
    "microcred/app/templates",
    "microcred/app/templates/participant",
    "microcred/app/templates/issuer",
    "microcred/app/templates/admin",
    "microcred/app/static",
    "microcred/app/static/awards",
    "microcred/instance",
]

# Zero-byte files – you fill in the implementation later
FILES = [
    # package markers
    "microcred/__init__.py",
    "microcred/app/__init__.py",
    "microcred/app/routes/__init__.py",
    "microcred/app/views/__init__.py",
    "microcred/app/models/__init__.py",
    "microcred/app/services/__init__.py",

    # config/boot
    "microcred/app/config.py",
    "microcred/app/extensions.py",
    "microcred/app/wsgi.py",

    # routes split by concern
    "microcred/app/routes/auth.py",
    "microcred/app/routes/participants.py",
    "microcred/app/routes/issuers.py",
    "microcred/app/routes/admin.py",
    "microcred/app/routes/api.py",

    # views (Jinja or helper classes; your call)
    "microcred/app/views/participants.py",
    "microcred/app/views/issuers.py",
    "microcred/app/views/admin.py",

    # models split by entity
    "microcred/app/models/user.py",
    "microcred/app/models/role.py",
    "microcred/app/models/award.py",
    "microcred/app/models/achievement.py",

    # templates (blank)
    "microcred/app/templates/base.html",
    "microcred/app/templates/login.html",
    "microcred/app/templates/register.html",
    "microcred/app/templates/participant/awards_list.html",
    "microcred/app/templates/participant/award_detail.html",
    "microcred/app/templates/issuer/awardable_list.html",
    "microcred/app/templates/issuer/issued_awards.html",
    "microcred/app/templates/admin/dashboard.html",

    # top-level helper files (blank)
    "requirements.txt",
    ".env",
    ".flaskenv",
    "README.md",
    "run.py",
]

AWARD_IMAGES = [
    "python_novice.png",
    "web_apprentice.png",
    "data_wrangler.png",
]

def make_tree():
    for d in DIRS:
        (ROOT / d).mkdir(parents=True, exist_ok=True)
    for f in FILES:
        p = ROOT / f
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.write_bytes(b"")  # zero-byte placeholder
    for name in AWARD_IMAGES:
        p = PKG / "static" / "awards" / name
        if not p.exists():
            p.write_bytes(b"")

def seed_db():
    INSTANCE.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON;")
    cur = con.cursor()

    # --- Schema (align your ORM to these names) ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT,
        first_name TEXT,
        last_name TEXT
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_roles (
        user_id INTEGER NOT NULL,
        role_id INTEGER NOT NULL,
        PRIMARY KEY (user_id, role_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS awards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        image_filename TEXT,
        points INTEGER NOT NULL DEFAULT 0,
        criteria TEXT
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        participant_id INTEGER NOT NULL,
        award_id INTEGER NOT NULL,
        issued_by_id INTEGER,               -- nullable so ON DELETE SET NULL works
        issued_at TEXT NOT NULL,
        note TEXT,
        UNIQUE (participant_id, award_id),
        FOREIGN KEY (participant_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (award_id) REFERENCES awards(id) ON DELETE CASCADE,
        FOREIGN KEY (issued_by_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    # --- Seed roles ---
    for role in ("participant", "issuer", "admin"):
        cur.execute("INSERT OR IGNORE INTO roles(name) VALUES (?);", (role,))
    con.commit()

    # Helper
    def get_id(table, where_col, val):
        row = cur.execute(f"SELECT id FROM {table} WHERE {where_col}=?;", (val,)).fetchone()
        return row[0] if row else None

    # --- Seed users ---
    users = [
        ("admin@example.com", "Site", "Admin", "hash:Passw0rd!"),
        ("issuer@example.com", "Issy", "Issuer", "hash:Passw0rd!"),
        ("alice@example.com", "Alice", "Participant", "hash:Passw0rd!"),
    ]
    for email, first, last, ph in users:
        cur.execute("""
            INSERT OR IGNORE INTO users(email, first_name, last_name, password_hash)
            VALUES (?, ?, ?, ?);
        """, (email, first, last, ph))
    con.commit()

    # --- Link roles ---
    links = [
        ("admin@example.com", "admin"),
        ("admin@example.com", "issuer"),
        ("issuer@example.com", "issuer"),
        ("alice@example.com", "participant"),
    ]
    for email, role in links:
        uid = get_id("users", "email", email)
        rid = get_id("roles", "name", role)
        if uid and rid:
            cur.execute("INSERT OR IGNORE INTO user_roles(user_id, role_id) VALUES (?,?);", (uid, rid))
    con.commit()

    # --- Seed awards ---
    awards = [
        ("python-novice", "Python Novice",
         "Completed intro Python module.", "python_novice.png", 10,
         "Finish: Variables, Loops, Conditionals; quiz ≥ 70%."),
        ("web-apprentice", "Web Apprentice",
         "Built a basic Flask app.", "web_apprentice.png", 20,
         "Deploy a working app with auth and one data model."),
        ("data-wrangler", "Data Wrangler",
         "Cleaned and analysed a dataset.", "data_wrangler.png", 30,
         "Upload notebook + summary; peer review passed."),
    ]
    for slug, name, desc, img, pts, crit in awards:
        cur.execute("""
            INSERT OR IGNORE INTO awards(slug, name, description, image_filename, points, criteria)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (slug, name, desc, img, pts, crit))
    con.commit()

    # --- Example achievement (Alice gets Python Novice from Admin) ---
    alice_id = get_id("users", "email", "alice@example.com")
    admin_id = get_id("users", "email", "admin@example.com")
    py_id = get_id("awards", "slug", "python-novice")
    if alice_id and admin_id and py_id:
        cur.execute("""
            INSERT OR IGNORE INTO achievements(participant_id, award_id, issued_by_id, issued_at, note)
            VALUES (?, ?, ?, ?, ?);
        """, (alice_id, py_id, admin_id, datetime.utcnow().isoformat(timespec="seconds"), "Initial seed"))
    con.commit()
    con.close()

def print_next_steps():
    print("\n✅ Done.")
    print("\nProject layout:")
    print(f"{ROOT.name}/")
    print("├─ microcred/")
    print("│  ├─ app/")
    print("│  │  ├─ routes/   (auth.py, participants.py, issuers.py, admin.py, api.py)")
    print("│  │  ├─ views/    (presentation helpers or class-based views)")
    print("│  │  ├─ models/   (user.py, role.py, award.py, achievement.py)")
    print("│  │  ├─ templates/ (+ subfolders)")
    print("│  │  ├─ static/awards/")
    print("│  │  ├─ config.py, extensions.py, wsgi.py, __init__.py")
    print("│  └─ instance/app.db  (pre-seeded)")
    print("├─ requirements.txt, .env, .flaskenv, run.py, README.md")
    print("\nNext steps (suggested):")
    print("  1) Build your Flask app inside microcred/app (__init__.py creates the app).")
    print("  2) Load config from .env and use the instance folder for the DB.")
    print("  3) Wire Blueprints from routes/*, and import models/* for SQLAlchemy.")
    print("  4) Replace the seeded schema with migrations later if you prefer.")

def main():
    print("Creating modern package structure with blank files…")
    make_tree()
    print(f"Creating and seeding database at {DB_PATH} …")
    seed_db()
    print_next_steps()

if __name__ == "__main__":
    main()
