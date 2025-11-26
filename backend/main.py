from fastapi import FastAPI, Depends, HTTPException, Request
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from config import settings
from database import engine, Base
from users.routers import router as user_router, get_db
from report_layouts.routers import router as layout_router
from users.services import get_user_by_email
from users.auth import verify_password, create_access_token
from users.schemas import UserLogin

# TODO: Remove for production   # # # # # # #
Base.metadata.create_all(bind=engine)
# # # # # # # # # # # # # #  # # # # # # #

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.include_router(user_router)
app.include_router(layout_router)


@app.post("/dash-login")
def dash_login(credentials: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = get_user_by_email(db, credentials.email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid login")
    token = create_access_token(user.id)
    return {"message": "Login successful", "access_token": token}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
