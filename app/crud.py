from sqlalchemy.orm import Session
from . import models, schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Utilisateur
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: Session, user: schemas.UserCreate):
    password = user.password[:72]  # bcrypt safety
    hashed_password = pwd_context.hash(password)
    db_user = models.User(email=user.email, pseudo=user.pseudo, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Messages
def get_messages(db: Session, user_id: int, skip: int = 0, limit: int = 20):
    return db.query(models.Message).filter(models.Message.receiver_id == user_id).order_by(models.Message.timestamp.desc()).offset(skip).limit(limit).all()


def create_message(db: Session, message: schemas.MessageCreate, sender_id: int):
    db_message = models.Message(
        content=message.content,
        media_url=message.media_url,
        media_type=message.media_type,
        receiver_id=message.receiver_id,
        sender_id=sender_id
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def mark_message_read(db: Session, message_id: int):
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if message and not message.read:
        message.read = True
        db.commit()
        db.refresh(message)
    return message
