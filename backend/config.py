"""
LedgerFlow AI — Configuration
Loads settings from environment variables / .env file.
"""
from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    # AWS
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    # Nova API
    nova_api_key: Optional[str] = None

    # Database
    database_url: str = "postgresql+asyncpg://ledgerflow:ledgerflow@localhost:5432/ledgerflow"

    # Storage
    s3_bucket: str = "ledgerflow-evidence"
    use_local_storage: bool = True
    local_storage_path: str = "./storage"

    # Nova Act
    nova_act_api_key: Optional[str] = None

    # Mock ERP
    mock_erp_url: str = "http://localhost:3001"

    # Bedrock Model IDs
    nova_lite_model_id: str = "us.amazon.nova-lite-v1:0"
    nova_embed_model_id: str = "amazon.nova-2-multimodal-embeddings-v1:0"

    # RAG
    embedding_dimensions: int = 1024
    rag_top_k: int = 5

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
