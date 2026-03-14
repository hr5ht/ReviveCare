"""
URL configuration for ReviveCare project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from Doctor import views as doctor
from Home import views as pages
from Patients.views import *


urlpatterns = [
    # Frontend pages (Backend/templates)
    path('', pages.home, name='home'),
    path('doctor/', doctor.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/login/', auth_views.LoginView.as_view(template_name='doctor_login.html', redirect_authenticated_user=True), name='doctor_login'),
    path('doctor/logout/', auth_views.LogoutView.as_view(next_page='doctor_login'), name='doctor_logout'),
    path('doctor/password-reset/', auth_views.PasswordResetView.as_view(
        email_template_name='registration/password_reset_email.txt',
        subject_template_name='registration/password_reset_subject.txt'), name='password_reset'),
    path('doctor/password-reset/sent/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('doctor/password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('doctor/password-reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('doctor/add-patient/', doctor.add_patient, name='add_patient'),
    path('doctor/profile/', doctor.doctor_profile, name='doctor_profile'),
    path('doctor/patients/<int:patient_id>/plan/', doctor.patient_plan, name='patient_plan'),
    path('doctor/patients/<int:patient_id>/goals/', doctor.patient_goals, name='patient_goals'),
    path('patient/', RedirectView.as_view(url='/patient/login/')),
    path('patient/login/', pages.patient_login, name='patient_login'),
    path('patient/dashboard/', pages.patient_dashboard, name='patient_dashboard_page'),
    path('patient/change-password/', pages.change_password, name='change_password'),
    path('patient/profile/', pages.patient_profile, name='patient_profile'),
    path('patient/history/', pages.workout_history, name='workout_history'),
    path('patient/forgot-password/', pages.patient_forgot_password, name='patient_forgot_password'),
    path('patient/reset-password/<str:token>/', pages.patient_reset_password, name='patient_reset_password'),
    path('patient/exercises/', pages.exercises, name='exercises'),
    path('patient/exercises/<slug:slug>/', pages.exercise_detail, name='exercise_detail'),
    path('patient/exercise/<str:exercise_id>/', pages.exercise_workout, name='exercise_workout'),
    path('patient/chat/', pages.chat, name='chat'),

    # Admin
    path('admin/', admin.site.urls),
    
    # JSON API endpoints
    path('api/', include('Patients.api_urls')),

    # Chatbot endpoint
    path('patient/chatbot/send/', chatbot_send, name='chatbot_send'),
]

