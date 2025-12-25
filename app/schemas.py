from pydantic import BaseModel
from datetime import datetime

# Base pour utilisateur
class UserBase(BaseModel):
    email: str
    pseudo: str

# Pour inscription
class UserCreate(UserBase):
    password: str

# Pour renvoyer un utilisateur
class User(UserBase):
    id: int
    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    email: str
    password: str


# Base pour message
class MessageBase(BaseModel):
    content: str | None = None       # texte optionnel
    media_url: str | None = None     # média optionnel
    media_type: str | None = None    # type optionnel
    receiver_id: int

# Pour créer un message
class MessageCreate(MessageBase):
    pass

# Pour renvoyer un message
class Message(MessageBase):
    id: int
    sender_id: int
    timestamp: datetime
    read: bool
    class Config:
        orm_mode = True
