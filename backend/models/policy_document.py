"""
PolicyDocument model — stores embedded policy documents for RAG retrieval.
"""
import uuid
from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from database import Base, TimestampMixin
from config import settings


class PolicyDocument(Base, TimestampMixin):
    __tablename__ = "policy_documents"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(50))
    # ap_tolerance | vendor_rules | tax_requirements | approval_hierarchy | general
    content: Mapped[str] = mapped_column(Text)
    metadata_extra: Mapped[dict] = mapped_column(JSON, nullable=True)
    embedding = mapped_column(Vector(settings.embedding_dimensions), nullable=True)
