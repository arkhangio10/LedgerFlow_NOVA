"""
Case model — core entity representing a financial exception case.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from database import Base, TimestampMixin


class Case(Base, TimestampMixin):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    case_type: Mapped[str] = mapped_column(String(50), default="invoice_exception")
    status: Mapped[str] = mapped_column(String(30), default="created")
    # created | processing | awaiting_approval | resolved | rejected | error
    submitted_by: Mapped[str] = mapped_column(String(100), default="analyst")
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    risk_level: Mapped[str] = mapped_column(String(20), default="low")
    title: Mapped[str] = mapped_column(String(200), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    final_outcome: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    evidences = relationship("Evidence", back_populates="case", cascade="all, delete-orphan")
    decision_steps = relationship("DecisionStep", back_populates="case", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="case", cascade="all, delete-orphan")
    ui_executions = relationship("UIExecution", back_populates="case", cascade="all, delete-orphan")
