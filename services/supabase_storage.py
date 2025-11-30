import os
import uuid
from functools import lru_cache
from typing import Optional

from django.conf import settings
from supabase import Client, create_client

BUCKET_NAME = "profile-pictures"


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Return a cached Supabase client configured from Django settings."""
    url = getattr(settings, "SUPABASE_URL", None)
    service_key = getattr(settings, "SUPABASE_SERVICE_KEY", None)
    if not url or not service_key:
        raise RuntimeError("Supabase URL/service key are not configured in environment variables")
    return create_client(url, service_key)


def build_profile_picture_path(student_number: str, original_filename: str) -> str:
    """Generate a unique storage path for a student's profile picture."""
    _, ext = os.path.splitext(original_filename)
    ext = ext.lower() or ".jpg"
    unique_name = f"{student_number}_{uuid.uuid4().hex}{ext}"
    return f"{BUCKET_NAME}/{student_number}/{unique_name}"


def upload_profile_picture(student_number: str, original_filename: str, file_data: bytes, content_type: Optional[str] = None) -> str:
    """Upload bytes to Supabase storage and return the public URL."""
    storage_path = build_profile_picture_path(student_number, original_filename)
    client = get_supabase_client()

    client.storage.from_(BUCKET_NAME).upload(
        storage_path,
        file_data,
        {
            "content-type": content_type or "application/octet-stream",
            "cache-control": "3600",
        },
    )

    public_url = client.storage.from_(BUCKET_NAME).get_public_url(storage_path)
    if not public_url:
        raise RuntimeError("Failed to retrieve public URL after uploading profile picture")
    return public_url
