# s3.py - Upload images to AWS S3
# Returns public URL or key for stored image

import logging
import uuid
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


def upload_file_to_s3(file_content: bytes, content_type: str, folder: str, original_filename: str) -> Optional[str]:
    """
    Upload file to S3. folder = "lost" or "found".
    Returns URL (or key) for the uploaded file, or None on failure.
    """
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY or not settings.S3_BUCKET:
        logger.warning("S3 not configured. Skipping upload.")
        return None

    try:
        import boto3
        from botocore.exceptions import ClientError

        ext = original_filename.split(".")[-1] if "." in original_filename else "jpg"
        key = f"uploads/{folder}/{uuid.uuid4().hex}.{ext}"

        s3 = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        s3.put_object(
            Bucket=settings.S3_BUCKET,
            Key=key,
            Body=file_content,
            ContentType=content_type,
        )
        # Public URL (if bucket is public) or use presigned URL for private buckets
        url = f"https://{settings.S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
        return url
    except ClientError as e:
        logger.exception("S3 upload failed: %s", e)
        return None
