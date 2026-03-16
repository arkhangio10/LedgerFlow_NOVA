"""
LedgerFlow AI — RAG Service
pgvector-based policy retrieval using Nova Multimodal Embeddings.
"""
import logging
from typing import Optional
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from models.policy_document import PolicyDocument
from services.bedrock_client import bedrock_client
from config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """Retrieval-Augmented Generation service for policy documents."""

    async def index_policy(
        self,
        session: AsyncSession,
        title: str,
        category: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> PolicyDocument:
        """
        Embed and index a policy document.
        
        Args:
            session: Database session
            title: Policy title
            category: Policy category (ap_tolerance, vendor_rules, etc.)
            content: Full policy text
            metadata: Additional metadata
        
        Returns:
            Created PolicyDocument
        """
        # Generate embedding
        embedding = await bedrock_client.get_embedding(text=content)

        doc = PolicyDocument(
            title=title,
            category=category,
            content=content,
            metadata_extra=metadata or {},
            embedding=embedding,
        )
        session.add(doc)
        await session.flush()
        logger.info(f"Indexed policy: {title} ({category})")
        return doc

    async def search_policies(
        self,
        session: AsyncSession,
        query: str,
        top_k: int = None,
        category: Optional[str] = None,
    ) -> list[dict]:
        """
        Search for relevant policies using cosine similarity.
        
        Args:
            session: Database session
            query: Search query text
            top_k: Number of results to return
            category: Optional filter by category
        
        Returns:
            List of matching policy dicts with score
        """
        top_k = top_k or settings.rag_top_k

        # Generate query embedding
        query_embedding = await bedrock_client.get_embedding(text=query)

        # Build pgvector cosine similarity query
        embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"

        if category:
            query_sql = text(
                f"""
                SELECT id, title, category, content, metadata_extra,
                       1 - (embedding <=> CAST(:embedding AS vector)) as similarity
                FROM policy_documents
                WHERE category = :category
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :top_k
                """
            )
            result = await session.execute(
                query_sql,
                {"embedding": embedding_str, "category": category, "top_k": top_k},
            )
        else:
            query_sql = text(
                f"""
                SELECT id, title, category, content, metadata_extra,
                       1 - (embedding <=> CAST(:embedding AS vector)) as similarity
                FROM policy_documents
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :top_k
                """
            )
            result = await session.execute(
                query_sql, {"embedding": embedding_str, "top_k": top_k}
            )

        rows = result.fetchall()
        policies = []
        for row in rows:
            policies.append(
                {
                    "id": row.id,
                    "title": row.title,
                    "category": row.category,
                    "content": row.content,
                    "metadata": row.metadata_extra,
                    "similarity": float(row.similarity),
                }
            )

        logger.info(f"RAG search: query='{query[:50]}...' results={len(policies)}")
        return policies


rag_service = RAGService()
