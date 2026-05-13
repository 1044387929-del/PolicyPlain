from datetime import datetime
from typing import Optional

from pwdlib import PasswordHash
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import Base

password_hasher = PasswordHash.recommended()


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    _password: Mapped[str] = mapped_column("password_hash", String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    explanations: Mapped[list["PolicyExplanationModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __init__(self, **kwargs):
        if "password" in kwargs:
            raw = kwargs.pop("password")
            kwargs["_password"] = password_hasher.hash(raw)
        super().__init__(**kwargs)

    def check_password(self, password: str) -> bool:
        return password_hasher.verify(password, self._password)


class PolicyExplanationModel(Base):
    __tablename__ = "policy_explanations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    topic: Mapped[str] = mapped_column(String(32), nullable=False, default="general")
    input_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    input_digest: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    result_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["UserModel"] = relationship(back_populates="explanations")
    followups: Mapped[list["PolicyFollowupModel"]] = relationship(
        back_populates="explanation",
        cascade="all, delete-orphan",
        order_by="PolicyFollowupModel.turn_index",
    )


class PolicyFollowupModel(Base):
    __tablename__ = "policy_followups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    explanation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("policy_explanations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    explanation: Mapped["PolicyExplanationModel"] = relationship(back_populates="followups")
