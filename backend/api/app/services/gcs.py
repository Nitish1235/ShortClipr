"""
Google Cloud Storage service — signed URLs, uploads, downloads
"""
import uuid
from datetime import timedelta
from typing import Optional

from google.cloud import storage
from google.oauth2 import service_account

from app.config import settings

_client: Optional[storage.Client] = None


def get_gcs_client() -> storage.Client:
    global _client
    if _client is None:
        if settings.GOOGLE_APPLICATION_CREDENTIALS:
            credentials = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_APPLICATION_CREDENTIALS
            )
            _client = storage.Client(
                project=settings.GCP_PROJECT_ID, credentials=credentials
            )
        else:
            # Use default Application Default Credentials (Cloud Run uses workload identity)
            _client = storage.Client(project=settings.GCP_PROJECT_ID)
    return _client


def generate_signed_upload_url(
    user_id: str,
    filename: str,
    content_type: str = "video/mp4",
    expiration_minutes: int = 60,
) -> dict:
    """
    Generate a v4 signed URL for direct client → GCS upload.
    Returns: { url, gcs_path, expiration }
    """
    client = get_gcs_client()
    bucket = client.bucket(settings.GCS_BUCKET_INPUT)

    # Structured path: users/{user_id}/uploads/{uuid}/{filename}
    file_uuid = str(uuid.uuid4())
    gcs_path = f"users/{user_id}/uploads/{file_uuid}/{filename}"
    blob = bucket.blob(gcs_path)

    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=expiration_minutes),
        method="PUT",
        content_type=content_type,
    )

    return {
        "upload_url": signed_url,
        "gcs_path": gcs_path,
        "gcs_uri": f"gs://{settings.GCS_BUCKET_INPUT}/{gcs_path}",
        "expires_in": expiration_minutes * 60,
    }


def generate_signed_download_url(
    bucket_name: str,
    gcs_path: str,
    expiration_hours: int = 24,
) -> str:
    """Generate a v4 signed URL for reading a GCS object."""
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    return blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=expiration_hours),
        method="GET",
    )


def upload_file_to_gcs(
    local_path: str,
    bucket_name: str,
    gcs_path: str,
    content_type: str = "video/mp4",
    make_public: bool = False,
) -> str:
    """Upload a local file to GCS. Returns public URL or gs:// URI."""
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(local_path, content_type=content_type)
    if make_public:
        blob.make_public()
        return blob.public_url
    return f"gs://{bucket_name}/{gcs_path}"


def download_file_from_gcs(gcs_uri: str, local_path: str) -> str:
    """Download a GCS object to a local path. Returns local_path."""
    # Parse gs://bucket/path
    without_scheme = gcs_uri.replace("gs://", "")
    bucket_name, gcs_path = without_scheme.split("/", 1)
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    blob.download_to_filename(local_path)
    return local_path


def delete_gcs_object(bucket_name: str, gcs_path: str) -> None:
    """Delete an object from GCS."""
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    blob.delete(if_generation_match=None)


def blob_exists(bucket_name: str, gcs_path: str) -> bool:
    """Check if a GCS blob exists."""
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob   = bucket.blob(gcs_path)
    return blob.exists()


async def stream_upload_to_gcs(
    blob_name:    str,
    data:         bytes,
    content_type: str,
    bucket:       str,
) -> dict:
    """
    Upload raw bytes to GCS asynchronously (runs sync GCS call in threadpool).
    Returns { public_url, gcs_uri }.
    Used by POST /videos/upload for direct multipart uploads.
    """
    import asyncio
    from io import BytesIO

    def _sync_upload() -> dict:
        client     = get_gcs_client()
        bucket_obj = client.bucket(bucket)
        b          = bucket_obj.blob(blob_name)
        b.upload_from_file(BytesIO(data), content_type=content_type)
        b.make_public()
        return {
            "public_url": b.public_url,
            "gcs_uri":    f"gs://{bucket}/{blob_name}",
        }

    return await asyncio.to_thread(_sync_upload)
