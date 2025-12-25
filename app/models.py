from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    pseudo = Column(String, unique=True)

    # Messages envoyés par cet utilisateur
    sent_messages = relationship(
        "Message",
        back_populates="sender",
        foreign_keys="Message.sender_id"
    )

    # Messages reçus par cet utilisateur
    received_messages = relationship(
        "Message",
        back_populates="receiver",
        foreign_keys="Message.receiver_id"
    )

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=True)         # texte du message
    media_url = Column(String, nullable=True)       # lien ou chemin vers média
    media_type = Column(String, nullable=True)      # type : 'image', 'video', 'pdf', 'link'
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    read = Column(Boolean, default=False)

    # Relations pour naviguer entre expéditeur/destinataire
    sender = relationship("User", back_populates="sent_messages", foreign_keys=[sender_id])
    receiver = relationship("User", back_populates="received_messages", foreign_keys=[receiver_id])
