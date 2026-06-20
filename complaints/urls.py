# complaints/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='complaints/login.html',
        redirect_authenticated_user=True,
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('notifications/', views.notifications, name='notifications'),
    path('users/', views.manage_users, name='manage_users'),
    path('complaint/create/', views.create_complaint, name='create_complaint'),
    path('complaint/<int:pk>/', views.complaint_detail, name='complaint_detail'),
    path('complaint/reopen/<int:pk>/', views.reopen_complaint, name='reopen_complaint'),
    path('complaint/update/<int:pk>/', views.update_status, name='update_status'),
    path('complaint/delete/<int:pk>/', views.delete_complaint, name='delete_complaint'),
    path('reports/', views.reports, name='reports'),
    path('export/', views.export_complaints_csv, name='export_csv'),

    # Password management routes
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='complaints/password_change_form.html',
        success_url='/password_change/done/'
    ), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='complaints/password_change_done.html'
    ), name='password_change_done'),
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='complaints/password_reset_form.html',
        email_template_name='complaints/password_reset_email.html',
        success_url='/password_reset/done/'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='complaints/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='complaints/password_reset_confirm.html',
        success_url='/reset/done/'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='complaints/password_reset_complete.html'
    ), name='password_reset_complete'),
]
