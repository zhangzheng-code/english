from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "User"

    id: str = Field(primary_key=True)
    name: str
    email: Optional[str] = Field(default=None)
    phone: str
    address: Optional[str] = Field(default=None)
    password: str
    avatar: Optional[str] = Field(default=None)
    bio: Optional[str] = Field(default=None)
    is_timing_task: bool = Field(
        default=False,
        sa_column=Column("isTimingTask", Boolean, default=False),
    )
    timing_task_time: str = Field(
        default="00:00:00",
        sa_column=Column("timingTaskTime", String, default="00:00:00"),
    )
    word_number: int = Field(
        default=0,
        sa_column=Column("wordNumber", Integer, default=0),
    )
    day_number: int = Field(
        default=0,
        sa_column=Column("dayNumber", Integer, default=0),
    )
    created_at: datetime = Field(sa_column=Column("createdAt", DateTime))
    updated_at: datetime = Field(sa_column=Column("updatedAt", DateTime))
    last_login_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column("lastLoginAt", DateTime, nullable=True),
    )

    word_book_records: List["WordBookRecord"] = Relationship(back_populates="user")
    user_files: List["UserFile"] = Relationship(back_populates="user")


class WordBook(SQLModel, table=True):
    __tablename__ = "WordBook"

    id: str = Field(primary_key=True)
    word: str
    phonetic: Optional[str] = Field(default=None)
    definition: Optional[str] = Field(default=None)
    translation: Optional[str] = Field(default=None)
    pos: Optional[str] = Field(default=None)
    collins: Optional[str] = Field(default=None)
    oxford: Optional[str] = Field(default=None)
    tag: Optional[str] = Field(default=None)
    bnc: Optional[str] = Field(default=None)
    frq: Optional[str] = Field(default=None)
    exchange: Optional[str] = Field(default=None)
    gk: Optional[bool] = Field(default=None)
    zk: Optional[bool] = Field(default=None)
    gre: Optional[bool] = Field(default=None)
    toefl: Optional[bool] = Field(default=None)
    ielts: Optional[bool] = Field(default=None)
    cet6: Optional[bool] = Field(default=None)
    cet4: Optional[bool] = Field(default=None)
    ky: Optional[bool] = Field(default=None)
    created_at: datetime = Field(sa_column=Column("createdAt", DateTime))
    updated_at: datetime = Field(sa_column=Column("updatedAt", DateTime))

    word_book_records: List["WordBookRecord"] = Relationship(back_populates="word")


class WordBookRecord(SQLModel, table=True):
    __tablename__ = "WordBookRecord"

    id: str = Field(primary_key=True)
    word_id: str = Field(
        sa_column=Column("wordId", String, ForeignKey("WordBook.id")),
    )
    is_master: bool = Field(
        default=False,
        sa_column=Column("isMaster", Boolean, default=False),
    )
    created_at: datetime = Field(sa_column=Column("createdAt", DateTime))
    updated_at: datetime = Field(sa_column=Column("updatedAt", DateTime))
    user_id: str = Field(
        sa_column=Column("userId", String, ForeignKey("User.id")),
    )

    user: Optional[User] = Relationship(back_populates="word_book_records")
    word: Optional[WordBook] = Relationship(back_populates="word_book_records")


class UserFile(SQLModel, table=True):
    __tablename__ = "UserFile"

    id: str = Field(primary_key=True)
    user_id: str = Field(
        sa_column=Column("userId", String, ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    )
    filename: str
    md5: str = Field(index=True)
    size: int
    url: str
    status: str = Field(default="processing")
    created_at: datetime = Field(sa_column=Column("createdAt", DateTime, default=datetime.utcnow))
    updated_at: datetime = Field(sa_column=Column("updatedAt", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow))

    user: Optional[User] = Relationship(back_populates="user_files")


class Course(SQLModel, table=True):
    __tablename__ = "Course"

    id: str = Field(primary_key=True)
    name: str
    value: str
    description: Optional[str] = Field(default=None)
    teacher: str
    url: str
    price: float
    created_at: datetime = Field(sa_column=Column("createdAt", DateTime, default=datetime.utcnow))
    updated_at: datetime = Field(sa_column=Column("updatedAt", DateTime, default=datetime.utcnow))


