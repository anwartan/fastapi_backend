from datetime import datetime
from sqlmodel import SQLModel, Field


class AIConversation(SQLModel, table=True):
    __tablename__ = "ai_conversation"

    ID: int | None = Field(default=None, primary_key=True)
    UserID: int = Field(index=True)
    Title: str = Field(max_length=255)
    CreatedAt: datetime = Field(default_factory=datetime.now)
    UpdatedAt: datetime = Field(default_factory=datetime.now)
    IsArchived: bool = Field(default=False)