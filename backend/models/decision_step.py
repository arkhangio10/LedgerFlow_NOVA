"""
DecisionStep model — structured trace of each agent decision in a workflow.
"""
import uuid
from sqlalchemy import String, Text, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from database import Base, TimestampMixin


class DecisionStep(Base, TimestampMixin):
    __tablename__ = "decision_steps"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    case_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("cases.id", ondelete="CASCADE")
    )
    step_number: Mapped[int] = mapped_column(default=0)
    agent_name: Mapped[str] = mapped_column(String(50))
    step_type: Mapped[str] = mapped_column(String(50))
    # ingest | parse | retrieve | validate | reason | human_gate | execute_ui | verify | close | emit_trace
    objective: Mapped[str] = mapped_column(Text, nullable=True)
    input_summary: Mapped[str] = mapped_column(Text, nullable=True)
    tool_called: Mapped[str] = mapped_column(String(100), nullable=True)
    policy_refs: Mapped[list] = mapped_column(JSON, nullable=True)
    evidence_refs: Mapped[list] = mapped_column(JSON, nullable=True)
    result_summary: Mapped[str] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="completed")
    # completed | pending | failed | skipped

    # Relationship
    case = relationship("Case", back_populates="decision_steps")
