"""
LedgerFlow AI — Storage Service
Handles file storage for evidence (local filesystem for MVP, S3-ready).
"""
import os
import uuid
import aiofiles
import logging
from config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """File storage for evidence documents, screenshots, etc."""

    def __init__(self):
        self.use_local = settings.use_local_storage
        self.local_path = settings.local_storage_path
        if self.use_local:
            os.makedirs(self.local_path, exist_ok=True)

    async def upload_file(
        self, file_bytes: bytes, filename: str, folder: str = "evidence"
    ) -> str:
        """
        Upload a file and return the storage path.
        
        Args:
            file_bytes: Raw file content
            filename: Original filename
            folder: Storage subfolder
        
        Returns:
            Storage path / URI
        """
        # Generate unique filename
        ext = os.path.splitext(filename)[1]
        unique_name = f"{uuid.uuid4()}{ext}"

        if self.use_local:
            return await self._upload_local(file_bytes, unique_name, folder)
        else:
            return await self._upload_s3(file_bytes, unique_name, folder)

    async def _upload_local(self, file_bytes: bytes, filename: str, folder: str) -> str:
        """Store file on local filesystem."""
        dir_path = os.path.join(self.local_path, folder)
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, filename)

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_bytes)

        logger.info(f"Stored file locally: {file_path}")
        return file_path

    async def _upload_s3(self, file_bytes: bytes, filename: str, folder: str) -> str:
        """Store file on S3."""
        import boto3
        s3 = boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        key = f"{folder}/{filename}"
        s3.put_object(Bucket=settings.s3_bucket, Key=key, Body=file_bytes)
        uri = f"s3://{settings.s3_bucket}/{key}"
        logger.info(f"Stored file on S3: {uri}")
        return uri

    async def read_file(self, file_path: str) -> bytes:
        """Read a file from storage."""
        if file_path.startswith("s3://"):
            return await self._read_s3(file_path)
        else:
            async with aiofiles.open(file_path, "rb") as f:
                return await f.read()

    async def _read_s3(self, uri: str) -> bytes:
        """Read file from S3."""
        import boto3
        s3 = boto3.client("s3", region_name=settings.aws_region)
        parts = uri.replace("s3://", "").split("/", 1)
        bucket, key = parts[0], parts[1]
        response = s3.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()


storage_service = StorageService()
