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
from Home.views import * 
from Doctor.views import *
from Patients.views import *


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API endpoints for React frontend (JSON responses)
    path('api/', include('Patients.api_urls')),
    
    # Original HTML template-based views - DISABLED
    # path('', home, name="home"),
    # path('doc_port/', doc_port, name="doc_port"),
    # path('doc_info_page/', doc_info_page, name="doc_info_page"),
    # path('doctor_info', doctor_info, name='doctor_info'),
    # path('login/', login, name='login'),  # This now handles patient login
    # path('patient/dashboard/', patient_dashboard, name='patient_dashboard'),
    # path('patient/logout/', patient_logout, name='patient_logout'),
    # path('patient/chatbot/', chatbot, name='chatbot'),
    path('patient/chatbot/send/', chatbot_send, name='chatbot_send'),
    # path('exercise', exercise , name = 'exercise'),
    # path('bc', bc , name = 'bc'),
    # path('jj', jj , name = 'jj'),
    # path('ar', ar , name = 'ar'),
    # path('sr', sr, name='sr'),  # Main tracker page
    # path('srtwo', srtwo, name='srtwo'),
    path('sr/video_feed/', video_feed, name='video_feed'),  # Video streaming
    path('sr/start/', start_workout, name='start_workout'),
    path('sr/reset/', reset_workout, name='reset_workout'),
    path('sr/status/', get_workout_status, name='get_workout_status'),
    path('sr/save/', save_workout, name='save_workout'),
    
    # Bicep Curl Endpoints
    path('bc/start/', start_bicep_workout, name='start_bicep_workout'),
    path('bc/reset/', reset_bicep_workout, name='reset_bicep_workout'),
    path('bc/status/', get_bicep_status, name='get_bicep_status'),
    path('bc/video_feed/', bicep_feed_view, name='bicep_feed_view'),
]

