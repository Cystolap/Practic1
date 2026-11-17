from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    role = Column(String(20), default="client")
    
    full_name = Column(String(255), default="")
    phone = Column(String(50), default="")


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    board_type = Column(String(20), default="ordinary")
    labels = Column(String(255), default="")
    
    master_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    boards = relationship("Board", cascade="all, delete-orphan")


class Board(Base):
    __tablename__ = "boards"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    columns = relationship("BoardColumn", cascade="all, delete-orphan")


class BoardColumn(Base):
    __tablename__ = "columns"
    id = Column(Integer, primary_key=True)
    board_id = Column(Integer, ForeignKey("boards.id"), nullable=False)
    name = Column(String(255), nullable=False)
    position = Column(Integer, default=0)
    wip_limit = Column(Integer, nullable=True)
    cards = relationship("Card", cascade="all, delete-orphan")


class Card(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True)
    column_id = Column(Integer, ForeignKey("columns.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    priority = Column(String(20), default="Средний")
    assignee_id = Column("assigne_id", Integer, ForeignKey("users.id"), nullable=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    deadline = Column(DateTime, nullable=True)
    labels = Column(String(255), default="")
    photo_url = Column(Text, default="")
    master_notes = Column(Text, default="")
    estimated_price = Column(Numeric(10, 2), nullable=True)
    position = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    comments = relationship("Comment", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class History(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
