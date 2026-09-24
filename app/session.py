import os

from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware


load_dotenv()


def add_session_middleware(app):

    secret_key = os.getenv(
        "SESSION_SECRET_KEY"
    )

    if not secret_key:
        raise RuntimeError(
            "SESSION_SECRET_KEY must be set."
        )

    app.add_middleware(
        SessionMiddleware,
        secret_key=secret_key,
        session_cookie="delivery_session",
        max_age=60 * 60 * 8,
        same_site="lax",
        https_only=False,
    )
    
from starlette.middleware.sessions import SessionMiddleware


SESSION_SECRET_KEY = "change-this-in-production"


def add_session_middleware(app):
    app.add_middleware(
        SessionMiddleware,
        secret_key=SESSION_SECRET_KEY,
        session_cookie="delivery_session",
        max_age=60 * 60 * 8,
        same_site="lax",
        https_only=False,
    )