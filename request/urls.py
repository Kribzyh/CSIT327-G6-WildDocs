from django.urls import path
from . import views

app_name = 'Request'

urlpatterns = [
    # Main request views
    path('pending/', views.requests_pending, name='pending'),
    path('approved/', views.requests_approved, name='approved'),
    path('completed/', views.requests_completed, name='completed'),
    path('detail/<int:request_id>/', views.request_detail, name='detail'),
    
    # Additional functionality
    path('pending/cancel/<int:request_id>/', views.cancel_pending_request, name='cancel_pending'),
    path('approved/pickup-slip/<int:request_id>/', views.generate_pickup_slip, name='pickup_slip'),
    path('completed/receipt/<int:request_id>/', views.download_completion_receipt, name='completion_receipt'),
    path('completed/statistics/', views.request_statistics, name='statistics'),
    path('detail/<int:request_id>/timeline/', views.request_timeline, name='timeline'),
]