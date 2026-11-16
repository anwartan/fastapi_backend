from datetime import datetime
from typing import Literal

from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Text


class AIMessage(SQLModel, table=True):
    __tablename__ = "ai_message"

    ID: int | None = Field(default=None, primary_key=True)

    ConversationID: int = Field(
        foreign_key="ai_conversation.ID",
        index=True
    )

    UserID: int = Field(index=True)

    Role: str = Field(max_length=20)

    Content: str = Field(sa_column=Column(Text, nullable=False))

    Provider: str | None = Field(default=None, max_length=50)
    Model: str | None = Field(default=None, max_length=100)

    PromptTokens: int | None = None
    CompletionTokens: int | None = None

    CreatedAt: datetime = Field(default_factory=datetime.now)