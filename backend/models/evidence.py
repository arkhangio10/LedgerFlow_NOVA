"""
Evidence model — uploaded files and parsed metadata attached to a case.
"""
import uuid
from sqlalchemy import String, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from database import Base, TimestampMixin


class Evidence(Base, TimestampMixin):
    __tablename__ = "evidences"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    case_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("cases.id", ondelete="CASCADE")
    )
    evidence_type: Mapped[str] = mapped_column(String(30))
    # pdf | image | audio | email | screenshot | text
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str] = mapped_column(String(100), nullable=True)
    parsed_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Relationship
    case = relationship("Case", back_populates="evidences")
