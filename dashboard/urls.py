from django.urls import path
from . import views

urlpatterns = [
    # Base student dashboard route
    path('', views.dashboard_redirect, name='dashboard'),

    # Student routes
    path('student_profile/', views.student_profile, name='student_profile'),
    path('requested_documents/', views.requested_documents, name='requested_documents'),
    path('requested_documents/<int:request_id>/requirements/', views.submit_requirements, name='submit_requirements'),
    path('requested_documents/<int:request_id>/requirement-uploads/', views.get_requirement_uploads, name='get_requirement_uploads'),
    path('requested_documents/<int:request_id>/payment/', views.submit_payment_receipt, name='submit_payment_receipt'),
    path('requested_documents/requirement-upload/<int:upload_id>/delete/', views.delete_requirement_upload, name='delete_requirement_upload'),
    path('history/', views.history, name='history'),
    path('about_us/', views.about_us, name='about_us'),
    path('faqs/', views.faqs, name='faqs'),
    path("request/cancel/<int:request_id>/", views.cancel_request, name="cancel_request"),
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('api/student-requests/', views.get_student_requests, name='get_student_requests'),

    # Admin routes
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-document-requests/', views.admin_document_requests, name='admin_document_requests'),
    path('admin-manage-students/', views.admin_manage_students, name='admin_manage_students'),
    path('admin-settings/', views.admin_settings, name='admin_settings'),
    path('admin-request-action/', views.admin_request_action, name='admin_request_action'),
    path('admin-request-detail/', views.admin_request_detail, name='admin_request_detail'),
    path('admin-debug-echo/', views.admin_debug_echo, name='admin_debug_echo'),
    path('save_request_instructions/', views.save_request_instructions, name='save_request_instructions'),
]

