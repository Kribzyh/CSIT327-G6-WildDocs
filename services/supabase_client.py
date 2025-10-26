import os
import requests
from django.conf import settings

SUPABASE_URL = getattr(settings, 'SUPABASE_URL', os.getenv('SUPABASE_URL'))
SUPABASE_SERVICE_KEY = getattr(settings, 'SUPABASE_SERVICE_KEY', os.getenv('SUPABASE_SERVICE_KEY'))

def check_user_exists(email):
    """Check if a user exists in Supabase Auth"""
    url = f"{SUPABASE_URL}/auth/v1/admin/users"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        users_data = resp.json()
        
        # Check if email exists in any user
        for user in users_data.get('users', []):
            if user.get('email', '').lower() == email.lower():
                return True, user
        return False, None
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Error checking user: {str(e)}"
        return False, error_msg

def create_user_admin(email, password, user_metadata=None):
    """Create a user in Supabase Auth via the Admin API."""
    url = f"{SUPABASE_URL}/auth/v1/admin/users"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
    }
    
    # Fixed payload - added email_confirm and proper structure
    payload = {
        "email": email, 
        "password": password,
        "email_confirm": True,  # This is crucial - auto-confirms the email
        "user_metadata": user_metadata or {}
    }
    
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        
        # Handle specific status codes
        if resp.status_code == 422:
            error_data = resp.json()
            error_msg = error_data.get('msg', 'Unprocessable Entity - check email format or password requirements')
            return None, error_msg
            
        if resp.status_code == 409:
            # User already exists
            return None, "User already exists"
            
        if resp.status_code == 400:
            error_data = resp.json()
            error_msg = error_data.get('message', 'Bad request - invalid data')
            return None, error_msg
            
        # For any other non-200 status, raise an error
        resp.raise_for_status()
        
        return resp.json(), None
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                error_msg = error_data.get('msg') or error_data.get('message') or str(e)
            except:
                error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
        return None, error_msg

def delete_user_admin(uid):
    """Delete a user in Supabase Auth via the Admin API."""
    url = f"{SUPABASE_URL}/auth/v1/admin/users/{uid}"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    }
    
    try:
        resp = requests.delete(url, headers=headers, timeout=10)
        if resp.status_code == 204:
            return True, None
        resp.raise_for_status()
        return False, f"Unexpected status code: {resp.status_code}"
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Delete failed: {str(e)}"
        return False, error_msg