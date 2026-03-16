"""
Approval model — human-in-the-loop approval records.
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from database import Base, TimestampMixin


class Approval(Base, TimestampMixin):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    case_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("cases.id", ondelete="CASCADE")
    )
    requested_to: Mapped[str] = mapped_column(String(100), default="supervisor")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending | approved | rejected
    decision_note: Mapped[str] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship
    case = relationship("Case", back_populates="approvals")
