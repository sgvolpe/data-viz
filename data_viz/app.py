# app.py
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.wsgi import WSGIMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from database import engine, Base
from users.routers import router as user_router, get_db
from report_layouts.routers import router as layout_router
from users.services import get_user_by_email
from users.auth import verify_password, create_access_token
from users.schemas import UserLogin
from dash_app import flask_server

# -----------------------------
# 1️⃣ FastAPI initialization
# -----------------------------
Base.metadata.create_all(bind=engine)
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="SUPER_SECRET_CHANGE_ME")
app.include_router(user_router)
app.include_router(layout_router)

# -----------------------------
# 6️⃣ Mount Flask/Dash under FastAPI
# -----------------------------
app.mount("/dash/", WSGIMiddleware(flask_server))


# -----------------------------
# 7️⃣ FastAPI login endpoint
# -----------------------------
@app.post("/dash-login")
def dash_login(credentials: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = get_user_by_email(db, credentials.email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid login")
    token = create_access_token(user.id)
    return {"message": "Login successful", "access_token": token}


# -----------------------------
# 8️⃣ Redirect /dash → /dash/
# -----------------------------
from fastapi.responses import RedirectResponse


@app.get("/dash")
def redirect_dash():
    return RedirectResponse("/dash/")


# -----------------------------
# 9️⃣ Run server
# -----------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
