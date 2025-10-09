import os
import requests
from django.conf import settings

SUPABASE_URL = getattr(settings, 'SUPABASE_URL', os.getenv('SUPABASE_URL'))
SUPABASE_SERVICE_KEY = getattr(settings, 'SUPABASE_SERVICE_KEY', os.getenv('SUPABASE_SERVICE_KEY'))

def create_user_admin(email, password, user_metadata=None):
    """Create a user in Supabase Auth via the Admin API."""
    url = f"{SUPABASE_URL}/auth/v1/admin/users"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"email": email, "password": password}
    if user_metadata:
        payload["user_metadata"] = user_metadata
    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    if resp.status_code == 409:
        # User already exists
        return None, "User already exists"
    resp.raise_for_status()
    return resp.json(), None

def delete_user_admin(uid):
    """Delete a user in Supabase Auth via the Admin API."""
    url = f"{SUPABASE_URL}/auth/v1/admin/users/{uid}"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    }
    resp = requests.delete(url, headers=headers, timeout=10)
    if resp.status_code == 204:
        return True
    resp.raise_for_status()
    return False