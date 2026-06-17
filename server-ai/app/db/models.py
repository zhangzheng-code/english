from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "User"

    id: str = Field(primary_key=True)
    name: str
    email: Optional[str] = Field(default=None, alias="email")
    phone: str
    password: str
    avatar: Optional[str] = Field(default=None, alias="avatar")
    bio: Optional[str] = Field(default=None, alias="bio")
    is_timing_task: bool = Field(default=False, alias="isTimingTask")
    timing_task_time: str = Field(default="00:00:00", alias="timingTaskTime")
    word_number: int = Field(default=0, alias="wordNumber")
    day_number: int = Field(default=0, alias="dayNumber")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    last_login_at: Optional[datetime] = Field(default=None, alias="lastLoginAt")

    word_book_records: list[WordBookRecord] = Relationship(back_populates="user")


class WordBook(SQLModel, table=True):
    __tablename__ = "WordBook"

    id: str = Field(primary_key=True)
    word: str
    phonetic: Optional[str] = Field(default=None, alias="phonetic")
    definition: Optional[str] = Field(default=None, alias="definition")
    translation: Optional[str] = Field(default=None, alias="translation")
    pos: Optional[str] = Field(default=None, alias="pos")
    collins: Optional[str] = Field(default=None, alias="collins")
    oxford: Optional[str] = Field(default=None, alias="oxford")
    tag: Optional[str] = Field(default=None, alias="tag")
    bnc: Optional[str] = Field(default=None, alias="bnc")
    frq: Optional[str] = Field(default=None, alias="frq")
    exchange: Optional[str] = Field(default=None, alias="exchange")
    gk: Optional[bool] = Field(default=None, alias="gk")
    zk: Optional[bool] = Field(default=None, alias="zk")
    gre: Optional[bool] = Field(default=None, alias="gre")
    toefl: Optional[bool] = Field(default=None, alias="toefl")
    ielts: Optional[bool] = Field(default=None, alias="ielts")
    cet6: Optional[bool] = Field(default=None, alias="cet6")
    cet4: Optional[bool] = Field(default=None, alias="cet4")
    ky: Optional[bool] = Field(default=None, alias="ky")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    word_book_records: list[WordBookRecord] = Relationship(back_populates="word")


class WordBookRecord(SQLModel, table=True):
    __tablename__ = "WordBookRecord"

    id: str = Field(primary_key=True)
    word_id: str = Field(alias="wordId")
    is_master: bool = Field(default=False, alias="isMaster")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    user_id: str = Field(alias="userId")

    user: Optional[User] = Relationship(back_populates="word_book_records")
    word: Optional[WordBook] = Relationship(back_populates="word_book_records")
