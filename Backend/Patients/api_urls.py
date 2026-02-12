# Patients/api_urls.py
# API URL patterns for React frontend

from django.urls import path
from . import api_views

urlpatterns = [
    # Health check
    path('health/', api_views.api_health, name='api_health'),
    
    # Patient authentication
    path('patient/login/', api_views.api_patient_login, name='api_patient_login'),
    path('patient/logout/', api_views.api_patient_logout, name='api_patient_logout'),
    path('patient/dashboard/', api_views.api_patient_dashboard, name='api_patient_dashboard'),
    path('patient/profile/', api_views.api_patient_profile, name='api_patient_profile'),
    
    # Exercises
    path('exercises/', api_views.api_exercise_list, name='api_exercise_list'),
    path('exercises/history/', api_views.api_exercise_history, name='api_exercise_history'),
    path('exercises/update-session/', api_views.api_update_session_data, name='api_update_session_data'),
    
    # Doctor endpoints
    path('patients/', api_views.api_get_all_patients, name='api_get_all_patients'),
    path('patients/add/', api_views.api_add_patient, name='api_add_patient'),
]
