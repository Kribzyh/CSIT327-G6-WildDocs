from django.urls import path
from . import views
from dashboard import views as dashboard_views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout, name='logout'),

    # Temporary admin dashboard route
    path('admin-dashboard/', dashboard_views.admin_dashboard, name='admin_dashboard'),
]