"""
UIExecution model — records of Nova Act browser automation actions.
"""
import uuid
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from database import Base, TimestampMixin


class UIExecution(Base, TimestampMixin):
    __tablename__ = "ui_executions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    case_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("cases.id", ondelete="CASCADE")
    )
    target_system: Mapped[str] = mapped_column(String(100), default="mock_erp")
    action_summary: Mapped[str] = mapped_column(Text, nullable=True)
    screenshot_before: Mapped[str] = mapped_column(String(500), nullable=True)
    screenshot_after: Mapped[str] = mapped_column(String(500), nullable=True)
    outcome: Mapped[str] = mapped_column(String(30), default="pending")
    # pending | success | failure | skipped
    error_detail: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationship
    case = relationship("Case", back_populates="ui_executions")
