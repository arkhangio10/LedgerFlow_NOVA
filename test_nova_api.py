import asyncio
import os
from backend.services.bedrock_client import bedrock_client
from backend.config import settings

async def main():
    print(f"KEY: {settings.nova_api_key}")
    res = await bedrock_client.invoke_nova_lite([{"role": "user", "content": "Hello!"}])
    print("SUCCESS")
    print(res)

if __name__ == "__main__":
    asyncio.run(main())
