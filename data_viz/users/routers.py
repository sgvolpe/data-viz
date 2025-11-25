# routers.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from users import schemas
from users import services
from users.auth import verify_password, create_access_token

router = APIRouter(prefix="/users", tags=["users"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/signup", response_model=schemas.UserRead)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if services.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return services.create_user(db, user)


@router.post("/login")
def login_user(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = services.get_user_by_email(db, credentials.email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}
