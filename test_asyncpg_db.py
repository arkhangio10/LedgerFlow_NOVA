import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Assuming db URL is postgresql+asyncpg://ledgerflow:ledgerflow@localhost:5432/ledgerflow
url = "postgresql+asyncpg://ledgerflow:ledgerflow@localhost:5432/ledgerflow"

async def main():
    engine = create_async_engine(url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # We will use dummy vectors of 1024 to match the expected settings
            embedding_str = f"[{','.join('0.0' for _ in range(1024))}]"
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
                query_sql, {"embedding": embedding_str, "top_k": 3}
            )
            rows = result.fetchall()
            print("SUCCESS! Found rows:", len(rows))
        except Exception as e:
            print("ERROR:")
            print(repr(e))

if __name__ == "__main__":
    asyncio.run(main())
