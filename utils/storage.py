"""AWS S3 storage helpers for uploading and downloading media files."""

import os
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from loguru import logger


class StorageError(Exception):
    """Raised when an S3 operation fails."""


class StorageClient:
    """Wraps boto3 S3 operations for media upload and download.

    Args:
        bucket_name: Name of the S3 bucket.
        region: AWS region name.
        aws_access_key_id: Optional explicit AWS access key.
        aws_secret_access_key: Optional explicit AWS secret key.
    """

    def __init__(
        self,
        bucket_name: str,
        region: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ) -> None:
        """Initialise the StorageClient with bucket and credentials."""
        self._bucket_name = bucket_name
        self._client = boto3.client(
            "s3",
            region_name=region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

    def upload_bytes(self, data: bytes, key: str, content_type: str = "application/octet-stream") -> str:
        """Upload raw bytes to S3 and return the public URL.

        Args:
            data: Raw bytes to upload.
            key: S3 object key (path within bucket).
            content_type: MIME type of the content.

        Returns:
            The public HTTPS URL of the uploaded object.
        """
        try:
            self._client.put_object(
                Bucket=self._bucket_name,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
            url = f"https://{self._bucket_name}.s3.amazonaws.com/{key}"
            logger.debug("Uploaded {} bytes to s3://{}/{}", len(data), self._bucket_name, key)
            return url
        except (BotoCoreError, ClientError) as error:
            logger.error("S3 upload failed for key {}: {}", key, error)
            raise StorageError(f"Upload failed for key '{key}'") from error

    def download_file(self, key: str, dest_path: str) -> str:
        """Download an S3 object to a local file path.

        Args:
            key: S3 object key to download.
            dest_path: Local file path where the object will be saved.

        Returns:
            The local file path of the downloaded object.
        """
        try:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            self._client.download_file(self._bucket_name, key, dest_path)
            logger.debug("Downloaded s3://{}/{} to {}", self._bucket_name, key, dest_path)
            return dest_path
        except (BotoCoreError, ClientError) as error:
            logger.error("S3 download failed for key {}: {}", key, error)
            raise StorageError(f"Download failed for key '{key}'") from error
