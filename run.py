"""
Dev entrypoint so you can simply:  python run.py
Relies on a factory at microcred/app/__init__.py named create_app().
"""
import os
from dotenv import load_dotenv

# Load .env before creating the app (so Config can see env vars)
load_dotenv()

# Import the factory (you'll add this file shortly)
from microcred.app import create_app  # type: ignore

app = create_app()

if __name__ == "__main__":
    # Respect FLASK_RUN_* if set; otherwise default to 127.0.0.1:5000
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_RUN_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") in {"1", "true", "True", "yes"}
    app.run(host=host, port=port, debug=debug)
