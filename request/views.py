"""
Main views module for the request app.
This file imports views from the organized view modules.
"""

# Import all views from the organized modules
from .views.pending import requests_pending, cancel_pending_request
from .views.approved import requests_approved, generate_pickup_slip
from .views.completed import requests_completed, download_completion_receipt, request_statistics
from .views.detail import request_detail, request_timeline

# Keep the original view functions for backward compatibility
# These are now imported from the respective modules above
