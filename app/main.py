from fastapi import FastAPI, Depends, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordBearer
from fastapi import status
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session
from dotenv import load_dotenv

import os
import uuid
import mimetypes
import shutil
import logging

from . import models, schemas, crud, database, auth


# Load environment variables
load_dotenv()
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# Create DB tables
models.Base.metadata.create_all(bind=database.engine)


# Initialize FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # ton frontend React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Database dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

MAX_FILE_SIZE = 15 * 1024 * 1024  # 15MB



# Endpoints

@app.post("/signup/", response_model=schemas.User)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, user.email)
    if db_user:
        logger.warning(f"Signup failed: email {user.email} already registered")
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = crud.create_user(db=db, user=user)
    logger.info(f"New user signed up: {user.email} (id={new_user.id})")
    return new_user

@app.post("/login/")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, user.email)
    if not db_user or not crud.verify_password(user.password, db_user.hashed_password):
        logger.warning(f"Failed login attempt for email: {user.email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid credentials")
    access_token = auth.create_access_token(data={"user_id": db_user.id})
    logger.info(f"User logged in: {user.email} (id={db_user.id})")
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/messages/", response_model=list[schemas.Message])
def get_messages(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    messages = crud.get_messages(db, user_id=current_user.id, skip=skip, limit=limit)
    for m in messages:
        crud.mark_message_read(db, m.id)
    logger.info(f"User {current_user.id} retrieved messages, skip={skip}, limit={limit}")
    return messages

@app.post("/messages/", response_model=schemas.Message)
def send_message(
    receiver_id: int,
    content: str | None = None,
    media: UploadFile | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    sender_id = current_user.id
    media_url = None
    media_type = None

    if media:
        # Vérification type MIME
        allowed_types = ["image/jpeg", "image/png", "video/mp4", "application/pdf"]
        if media.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="File type not allowed")
        
        # Limitation taille
        media.file.seek(0, 2)  # aller à la fin
        size = media.file.tell()
        if size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
        media.file.seek(0)

        # Renommer fichier pour éviter collision
        ext = mimetypes.guess_extension(media.content_type) or ""
        filename = f"{uuid.uuid4().hex}{ext}"
        file_path = f"{UPLOAD_DIR}/{filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(media.file, buffer)
        media_url = file_path
        media_type = media.content_type

    message_create = schemas.MessageCreate(
        content=content,
        media_url=media_url,
        media_type=media_type,
        receiver_id=receiver_id
    )
    msg = crud.create_message(db=db, message=message_create, sender_id=sender_id)
    logger.info(f"User {sender_id} sent message to {receiver_id}, media: {media_type}")
    return msg
