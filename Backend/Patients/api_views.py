# Patients/api_views.py
# JSON API views for React frontend integration
# These views return JSON responses instead of HTML templates

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Patient, SLS, BicepCurl, JumpingJack, ArmRaise
from django.utils import timezone
import json
from datetime import timedelta


def json_response_decorator(view_func):
    """Decorator to ensure JSON response with proper headers"""
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    return wrapper


# ============================================================================
# PATIENT API ENDPOINTS
# ============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def api_patient_login(request):
    """
    Patient login API endpoint
    Accepts email and creates session
    Returns JSON with success status and patient data
    """
    try:
        print(f"DEBUG: Login request body: {request.body.decode('utf-8')}")
        data = json.loads(request.body) if request.body else {}
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()
        print(f"DEBUG: Parsed data - Email: {email}, Password provided: {bool(password)}")
        
        if not email or not password:
            return JsonResponse({
                'success': False,
                'error': 'Email and password are required'
            }, status=400)
        
        try:
            patient = Patient.objects.get(email=email)
            
            # Simple password check (Note: use hashing in production!)
            if patient.password != password:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid email or password'
                }, status=401)
            
            # Create session
            request.session['patient_id'] = patient.id
            request.session['patient_email'] = patient.email
            request.session['patient_name'] = patient.name
            
            return JsonResponse({
                'success': True,
                'message': f'Welcome back, {patient.name}!',
                'patient': {
                    'id': patient.id,
                    'name': patient.name,
                    'email': patient.email,
                }
            })
            
        except Patient.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Doctor has not updated this email yet. Please come back later.'
            }, status=404)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)


@require_http_methods(["GET"])
def api_patient_dashboard(request):
    """
    Get patient dashboard data
    Returns patient profile and stats as JSON
    """
    patient_id = request.session.get('patient_id')
    
    if not patient_id:
        return JsonResponse({
            'success': False,
            'error': 'Not authenticated'
        }, status=401)
    
    try:
        patient = Patient.objects.get(id=patient_id)
        
        # Get exercise stats
        stats = {
            'total_sessions': 0,
            'total_reps': 0,
            'avg_quality': 0,
            'best_session_reps': 0,
        }
        
        try:
            from django.db.models import Sum, Max
            all_workouts = SLS.objects.filter(patient=patient)
            
            if all_workouts.exists():
                stats = {
                    'total_sessions': all_workouts.count(),
                    'total_reps': all_workouts.aggregate(Sum('total_reps'))['total_reps__sum'] or 0,
                    'avg_quality': round(sum([w.quality_score for w in all_workouts]) / all_workouts.count(), 1) if all_workouts.count() > 0 else 0,
                    'best_session_reps': all_workouts.aggregate(Max('total_reps'))['total_reps__max'] or 0,
                }
        except Exception as e:
            print(f"Error getting stats: {e}")
        
        return JsonResponse({
            'success': True,
            'patient': {
                'id': patient.id,
                'name': patient.name,
                'email': patient.email,
                'info': patient.info if hasattr(patient, 'info') else '',
            },
            'stats': stats
        })
        
    except Patient.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Patient not found'
        }, status=404)


@require_http_methods(["POST"])
def api_patient_logout(request):
    """Logout patient and clear session"""
    request.session.flush()
    return JsonResponse({
        'success': True,
        'message': 'Logged out successfully'
    })


@require_http_methods(["GET"])
def api_patient_profile(request):
    """Get current patient profile"""
    patient_id = request.session.get('patient_id')
    
    if not patient_id:
        return JsonResponse({
            'success': False,
            'error': 'Not authenticated'
        }, status=401)
    
    try:
        patient = Patient.objects.get(id=patient_id)
        return JsonResponse({
            'success': True,
            'patient': {
                'id': patient.id,
                'name': patient.name,
                'email': patient.email,
                'info': patient.info if hasattr(patient, 'info') else '',
            }
        })
    except Patient.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Patient not found'
        }, status=404)


# ============================================================================
# EXERCISE API ENDPOINTS
# ============================================================================

@require_http_methods(["GET"])
def api_exercise_list(request):
    """Get list of available exercises"""
    exercises = [
        {
            'id': 'sr',
            'name': 'Side Lateral Raise',
            'description': 'Shoulder strengthening exercise',
            'target_muscles': ['Shoulders', 'Deltoids'],
            'difficulty': 'Beginner',
            'video_url': '/sr/video_feed/',
        },
        {
            'id': 'ar',
            'name': 'Arm Raise',
            'description': 'Arm strengthening exercise',
            'target_muscles': ['Arms', 'Shoulders'],
            'difficulty': 'Beginner',
        },
        {
            'id': 'bc',
            'name': 'Bicep Curl',
            'description': 'Bicep strengthening exercise',
            'target_muscles': ['Biceps', 'Arms'],
            'difficulty': 'Beginner',
        },
        {
            'id': 'jj',
            'name': 'Jumping Jacks',
            'description': 'Full body cardio exercise',
            'target_muscles': ['Full Body'],
            'difficulty': 'Beginner',
        },
    ]
    
    return JsonResponse({
        'success': True,
        'exercises': exercises
    })


@require_http_methods(["GET"])
def api_exercise_history(request):
    """Get exercise history for logged-in patient"""
    patient_id = request.session.get('patient_id')
    
    if not patient_id:
        return JsonResponse({
            'success': False,
            'error': 'Not authenticated'
        }, status=401)
    
    try:
        patient = Patient.objects.get(id=patient_id)
        
        # Get recent workouts
        seven_days_ago = timezone.now().date() - timedelta(days=7)
        recent_workouts = SLS.objects.filter(
            patient=patient,
            date__gte=seven_days_ago
        ).order_by('-created_at')[:10]
        
        workouts = []
        for workout in recent_workouts:
            workouts.append({
                'id': workout.id,
                'date': workout.date.isoformat(),
                'total_reps': workout.total_reps,
                'target_reps': workout.target_reps,
                'excellent_reps': workout.excellent_reps,
                'good_reps': workout.good_reps,
                'partial_reps': workout.partial_reps,
                'completed': workout.completed,
                'duration_seconds': workout.duration_seconds,
                'quality_score': workout.quality_score,
            })
        
        return JsonResponse({
            'success': True,
            'workouts': workouts
        })
        
    except Patient.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Patient not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': True,
            'workouts': []
        })


@csrf_exempt
@require_http_methods(["POST"])
def api_update_session_data(request):
    """
    Update real-time angles and reps for an active session.
    Stores data in the database for later analysis.
    """
    patient_id = request.session.get('patient_id')
    if not patient_id:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    try:
        data = json.loads(request.body)
        exercise_id = data.get('exercise_id') 
        reps = data.get('reps', 0)
        angle = data.get('angle', 0)
        stage = data.get('stage', 'down')
        completed = data.get('completed', False)
        
        today = timezone.now().date()
        
        if exercise_id == 'bicep-curl':
            workout, created = BicepCurl.objects.get_or_create(
                patient_id=patient_id,
                date=today,
                completed=False,
                defaults={'target_reps': 10}
            )
            workout.total_reps = reps
            
            # Simple Quality Logic based on angle range
            if angle < 45:
                workout.excellent_reps = max(workout.excellent_reps, reps - (workout.good_reps + workout.partial_reps))
            elif angle < 60:
                workout.good_reps = max(workout.good_reps, reps - (workout.excellent_reps + workout.partial_reps))
            
            if not isinstance(workout.angles_data, list): workout.angles_data = []
            workout.angles_data.append({'time': timezone.now().isoformat(), 'angle': angle, 'stage': stage, 'rep': reps})
            if completed: workout.completed = True
            workout.save()
            
        elif exercise_id == 'shoulder-extension':
             workout, created = SLS.objects.get_or_create(
                patient_id=patient_id, date=today, completed=False, defaults={'target_reps': 12}
            )
             workout.total_reps = reps
             if angle > 80:
                 workout.excellent_reps = max(workout.excellent_reps, reps - (workout.good_reps + workout.partial_reps))
             elif angle > 65:
                 workout.good_reps = max(workout.good_reps, reps - (workout.excellent_reps + workout.partial_reps))
             
             if not isinstance(workout.angles_data, list): workout.angles_data = []
             workout.angles_data.append({'time': timezone.now().isoformat(), 'angle': angle, 'stage': stage, 'rep': reps})
             if completed: workout.completed = True
             workout.save()

        elif exercise_id == 'jumping-jacks':
             workout, created = JumpingJack.objects.get_or_create(
                patient_id=patient_id, date=today, completed=False, defaults={'target_reps': 20}
            )
             workout.total_reps = reps
             workout.excellent_reps = reps # Generic for now
             if not isinstance(workout.angles_data, list): workout.angles_data = []
             workout.angles_data.append({'time': timezone.now().isoformat(), 'angle': angle, 'stage': stage, 'rep': reps})
             if completed: workout.completed = True
             workout.save()

        elif exercise_id == 'arm-raises' or exercise_id == 'ar':
             workout, created = ArmRaise.objects.get_or_create(
                patient_id=patient_id, date=today, completed=False, defaults={'target_reps': 15}
            )
             workout.total_reps = reps
             if angle > 85:
                 workout.excellent_reps = max(workout.excellent_reps, reps - (workout.good_reps + workout.partial_reps))
             elif angle > 70:
                 workout.good_reps = max(workout.good_reps, reps - (workout.excellent_reps + workout.partial_reps))

             if not isinstance(workout.angles_data, list): workout.angles_data = []
             workout.angles_data.append({'time': timezone.now().isoformat(), 'angle': angle, 'stage': stage, 'rep': reps})
             if completed: workout.completed = True
             workout.save()

        return JsonResponse({'success': True, 'reps': reps})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============================================================================
# DOCTOR API ENDPOINTS
# ============================================================================

@require_http_methods(["GET"])
def api_get_all_patients(request):
    """Get all patients (for doctor dashboard)"""
    patients = Patient.objects.all()
    
    patient_list = []
    for patient in patients:
        patient_list.append({
            'id': patient.id,
            'name': patient.name,
            'email': patient.email,
            'info': patient.info if hasattr(patient, 'info') else '',
        })
    
    return JsonResponse({
        'success': True,
        'patients': patient_list
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_add_patient(request):
    """Add new patient (for doctor)"""
    try:
        data = json.loads(request.body) if request.body else {}
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        info = data.get('info', '').strip()
        
        if not name or not email:
            return JsonResponse({
                'success': False,
                'error': 'Name and email are required'
            }, status=400)
        
        # Check if patient already exists
        if Patient.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'error': 'Patient with this email already exists'
            }, status=400)
        
        patient = Patient.objects.create(
            name=name,
            email=email,
            info=info
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Patient added successfully',
            'patient': {
                'id': patient.id,
                'name': patient.name,
                'email': patient.email,
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)


# ============================================================================
# HEALTH CHECK
# ============================================================================

@require_http_methods(["GET"])
def api_health(request):
    """Health check endpoint - verifies backend and database are running"""
    db_ok = False
    db_error = None
    try:
        from django.db import connection
        connection.ensure_connection()
        db_ok = True
    except Exception as e:
        db_error = str(e)

    return JsonResponse({
        'success': db_ok,
        'status': 'ok' if db_ok else 'error',
        'db_connected': db_ok,
        'db_error': db_error,
        'message': 'ReviveCare API is running' if db_ok else 'Database connection error',
        'authenticated': bool(request.session.get('patient_id'))
    }, status=200 if db_ok else 503)
