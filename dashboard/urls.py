from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('student_profile/', views.student_profile, name='student_profile'),
    path('requested_documents/', views.requested_documents, name='requested_documents'),
    path('history/', views.history, name='history'),
    path('about_us/', views.about_us, name='about_us'),
    path('faqs/', views.faqs, name='faqs'),
]