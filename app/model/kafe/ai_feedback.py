from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Text


class AIFeedback(SQLModel, table=True):
    __tablename__ = "ai_feedback"

    ID: int | None = Field(default=None, primary_key=True)

    MessageID: int = Field(
        foreign_key="ai_message.ID",
        index=True
    )

    UserID: int = Field(index=True)

    Rating: int = Field(ge=1, le=5)

    Correction: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True)
    )

    Comment: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True)
    )

    Status: str = Field(
        default="pending",
        max_length=20
    )

    ReviewedBy: int | None = Field(default=None)

    CreatedAt: datetime = Field(
        default_factory=datetime.now
    )