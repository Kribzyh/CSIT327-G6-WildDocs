from django.urls import path
from . import views

urlpatterns = [
    # Base student dashboard route
    path('', views.dashboard_redirect, name='dashboard'),

    # Student routes
    path('student_profile/', views.student_profile, name='student_profile'),
    path('requested_documents/', views.requested_documents, name='requested_documents'),
    path('history/', views.history, name='history'),
    path('about_us/', views.about_us, name='about_us'),
    path('faqs/', views.faqs, name='faqs'),
    path("request/cancel/<int:request_id>/", views.cancel_request, name="cancel_request"),

    # Admin routes
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-document-requests/', views.admin_document_requests, name='admin_document_requests'),
    path('admin-manage-students/', views.admin_manage_students, name='admin_manage_students'),
    path('admin-settings/', views.admin_settings, name='admin_settings'),
    path('admin-request-action/', views.admin_request_action, name='admin_request_action'),
    path('admin-request-detail/', views.admin_request_detail, name='admin_request_detail'),
]

