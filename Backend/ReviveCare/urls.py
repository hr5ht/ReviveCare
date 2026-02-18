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
from django.views.generic import RedirectView
from Home import views as pages
from Patients.views import *


urlpatterns = [
    # Frontend pages (Backend/templates)
    path('', pages.home, name='home'),
    path('medical-dashboard/', pages.medical_dashboard, name='medical_dashboard'),
    path('doctor/', pages.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/add-patient/', pages.add_patient, name='add_patient'),
    path('patient/', RedirectView.as_view(url='/patient/login/')),
    path('patient/login/', pages.patient_login, name='patient_login'),
    path('patient/dashboard/', pages.patient_dashboard, name='patient_dashboard_page'),
    path('patient/change-password/', pages.change_password, name='change_password'),
    path('patient/exercises/', pages.exercises, name='exercises'),
    path('patient/exercise/<str:exercise_id>/', pages.exercise_workout, name='exercise_workout'),
    path('patient/chat/', pages.chat, name='chat'),
    path('chat/', pages.chat),

    # Admin
    path('admin/', admin.site.urls),
    
    # JSON API endpoints
    path('api/', include('Patients.api_urls')),

    # Chatbot endpoint
    path('patient/chatbot/send/', chatbot_send, name='chatbot_send'),
]

