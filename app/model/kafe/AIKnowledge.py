from datetime import datetime

from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.mysql import LONGTEXT


class AIKnowledge(SQLModel, table=True):
    __tablename__ = "ai_knowledge"

    ID: int | None = Field(
        default=None,
        primary_key=True
    )

    SourceFeedbackID: int | None = Field(
        default=None,
        foreign_key="ai_feedback.ID",
        unique=True,
        index=True
    )

    Title: str = Field(
        max_length=255,
        nullable=False
    )

    Content: str = Field(
        sa_column=Column(LONGTEXT, nullable=False)
    )

    Category: str | None = Field(
        default=None,
        max_length=100
    )

    Status: str = Field(
        default="active",
        max_length=20
    )

    CreatedBy: int | None = Field(
        default=None
    )

    CreatedAt: datetime = Field(
        default_factory=datetime.now
    )

    UpdatedAt: datetime = Field(
        default_factory=datetime.now
    )