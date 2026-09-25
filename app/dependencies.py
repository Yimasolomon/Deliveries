from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from fastapi.responses import RedirectResponse

from app.database import get_db
from app.models import User


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Inactive user",
        )

    return user

def require_login(
    request: Request,
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=303,
            headers={
                "Location": "/login",
            },
        )

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user or not user.is_active:
        request.session.clear()

        raise HTTPException(
            status_code=303,
            headers={
                "Location": "/login",
            },
        )

    return user