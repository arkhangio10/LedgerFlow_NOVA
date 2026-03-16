import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.services.rag import rag_service
from backend.config import settings

async def main():
    engine = create_async_engine(settings.database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            res = await rag_service.search_policies(session, "test query")
            print("SUCCESS", res)
        except Exception as e:
            print("ERROR:")
            print(repr(e))

if __name__ == "__main__":
    asyncio.run(main())
