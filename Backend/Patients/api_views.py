# Patients/api_views.py
# JSON API views
# These views return JSON responses instead of HTML templates

from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_http_methods
from .models import Patient, Workout
from django.utils import timezone
import json
from datetime import date, timedelta
import logging
from functools import wraps

logger = logging.getLogger(__name__)


def doctor_required(view):
    """JSON 401 unless a doctor (Django user) is logged in."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Doctor login required'}, status=401)
        return view(request, *args, **kwargs)
    return wrapper


# ============================================================================
# PATIENT API ENDPOINTS
# ============================================================================

LOGIN_FAILURE_LIMIT = 10
LOGIN_FAILURE_WINDOW = 15 * 60  # seconds


def _login_failures_key(request):
    # Vercel sets X-Real-IP to the client address; REMOTE_ADDR covers local runs
    ip = request.META.get('HTTP_X_REAL_IP') or request.META.get('REMOTE_ADDR', '')
    return f'patient-login-failures:{ip}'


def _record_login_failure(request):
    # ponytail: per-instance memory cache, so the limit is per server instance; use a shared cache if that matters
    key = _login_failures_key(request)
    cache.add(key, 0, LOGIN_FAILURE_WINDOW)
    cache.incr(key)


ACCOUNT_LOCK_AFTER = 5  # consecutive wrong passwords
ACCOUNT_LOCK_MINUTES = 15


@require_http_methods(["POST"])
def api_patient_login(request):
    """
    Patient login API endpoint
    Accepts email and creates session
    Returns JSON with success status and patient data
    """
    if cache.get(_login_failures_key(request), 0) >= LOGIN_FAILURE_LIMIT:
        return JsonResponse({
            'success': False,
            'error': 'Too many failed login attempts. Please try again in 15 minutes.'
        }, status=429)

    try:
        data = json.loads(request.body) if request.body else {}
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()

        if not email or not password:
            return JsonResponse({
                'success': False,
                'error': 'Email and password are required'
            }, status=400)
        
        try:
            patient = Patient.objects.get(email=email)

            if patient.locked_until and patient.locked_until > timezone.now():
                return JsonResponse({
                    'success': False,
                    'error': f'This account is locked after too many wrong passwords. Try again in {ACCOUNT_LOCK_MINUTES} minutes or ask your doctor.'
                }, status=423)

            if not check_password(password, patient.password):
                _record_login_failure(request)
                patient.failed_login_count += 1
                if patient.failed_login_count >= ACCOUNT_LOCK_AFTER:
                    patient.failed_login_count = 0
                    patient.locked_until = timezone.now() + timedelta(minutes=ACCOUNT_LOCK_MINUTES)
                patient.save(update_fields=['failed_login_count', 'locked_until'])
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid email or password'
                }, status=401)
            
            if patient.failed_login_count or patient.locked_until:
                patient.failed_login_count, patient.locked_until = 0, None
                patient.save(update_fields=['failed_login_count', 'locked_until'])

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
                },
                'must_change_password': patient.must_change_password,
            })
            
        except Patient.DoesNotExist:
            _record_login_failure(request)
            return JsonResponse({
                'success': False,
                'error': 'Doctor has not updated this email yet. Please come back later.'
            }, status=404)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)


@require_http_methods(["POST"])
def api_patient_logout(request):
    """Logout patient and clear session"""
    request.session.flush()
    return JsonResponse({
        'success': True,
        'message': 'Logged out successfully'
    })


@require_http_methods(["POST"])
def api_patient_change_password(request):
    """Change the logged-in patient's password (needs the current one)"""
    patient = Patient.objects.filter(id=request.session.get('patient_id')).first()
    if not patient:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)

    data = json.loads(request.body or '{}')
    current, new = data.get('current_password', ''), data.get('new_password', '')
    if not check_password(current, patient.password):
        return JsonResponse({'success': False, 'error': 'Current password is incorrect'}, status=400)
    if new == current:
        return JsonResponse({'success': False, 'error': 'New password must be different from the current one'}, status=400)
    try:
        validate_password(new)
    except ValidationError as e:
        return JsonResponse({'success': False, 'error': ' '.join(e.messages)}, status=400)

    patient.password = make_password(new)
    patient.must_change_password = False
    patient.save(update_fields=['password', 'must_change_password'])
    return JsonResponse({'success': True, 'message': 'Password updated'})


# ============================================================================
# EXERCISE API ENDPOINTS
# ============================================================================


QUALITY_FIELDS = {'excellent': 'excellent_reps', 'good': 'good_reps', 'partial': 'partial_reps'}


@require_http_methods(["POST"])
def api_update_session_data(request):
    """Save live workout progress: one Workout row per patient, exercise and day."""
    patient_id = request.session.get('patient_id')
    if not patient_id:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)

    try:
        data = json.loads(request.body)
        exercise = data.get('exercise_id')
        if not exercise:
            return JsonResponse({'success': False, 'error': 'exercise_id is required'}, status=400)
        reps = int(data.get('reps', 0))
        target_reps = data.get('target_reps')

        workout, _ = Workout.objects.get_or_create(
            patient_id=patient_id, exercise=exercise, date=timezone.localdate(), completed=False,
            defaults={'target_reps': int(target_reps or 10)},
        )
        if target_reps:
            workout.target_reps = int(target_reps)
        # Count a rep's quality once: only when the page reports a rep we haven't graded yet
        field = QUALITY_FIELDS.get(data.get('quality'))
        if field and reps > workout.excellent_reps + workout.good_reps + workout.partial_reps:
            setattr(workout, field, getattr(workout, field) + 1)
        workout.total_reps = reps
        workout.angles_data.append({'time': timezone.now().isoformat(), 'angle': data.get('angle', 0),
                                    'stage': data.get('stage', 'down'), 'rep': reps})
        if data.get('completed'):
            workout.completed = True
        workout.save()
        return JsonResponse({'success': True, 'reps': reps})

    except Exception:
        logger.exception('Saving workout session failed for patient %s', patient_id)
        return JsonResponse({'success': False, 'error': 'Could not save your workout progress'}, status=500)


# ============================================================================
# DOCTOR API ENDPOINTS
# ============================================================================

@require_http_methods(["GET"])
@doctor_required
def api_get_all_patients(request):
    """The logged-in doctor's patients"""
    patients = Patient.for_doctor(request.user)
    
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


def send_welcome_email(request, patient, temp_password):
    """Email a new patient their login details. Returns True if it was sent."""
    login_url = request.build_absolute_uri('/patient/login/')
    body = (
        f"Hi {patient.name},\n\n"
        "Your doctor has added you to ReViveCare, your post-discharge recovery companion.\n\n"
        f"Log in at: {login_url}\n"
        f"Email: {patient.email}\n"
        f"Temporary password: {temp_password}\n\n"
        "You'll be asked to choose your own password the first time you log in.\n\n"
        "— The ReViveCare team"
    )
    try:
        send_mail('Your ReViveCare login details', body, None, [patient.email])
        return True
    except Exception:
        logger.exception('Welcome email to patient %s failed', patient.id)
        return False


@require_http_methods(["POST"])
@doctor_required
def api_add_patient(request):
    """Add new patient (for doctor)"""
    try:
        data = json.loads(request.body) if request.body else {}
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        info = data.get('info', '').strip()
        extra = {f: str(data.get(f) or '').strip() for f in
                 ('condition', 'phone', 'emergency_contact_name', 'emergency_contact_phone')}
        try:
            surgery_date = date.fromisoformat(data['surgery_date']) if data.get('surgery_date') else None
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Surgery date must be a valid date'}, status=400)
        if surgery_date and surgery_date > timezone.localdate():
            return JsonResponse({'success': False, 'error': 'Surgery date cannot be in the future'}, status=400)
        
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
        
        # No look-alike characters (0/O, 1/l/I) so it's easy to read out to a patient
        temp_password = get_random_string(10, 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789')
        patient = Patient.objects.create(
            name=name,
            email=email,
            info=info,
            password=make_password(temp_password),
            must_change_password=True,
            doctor=request.user,
            surgery_date=surgery_date,
            **extra,
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Patient added successfully',
            'patient': {
                'id': patient.id,
                'name': patient.name,
                'email': patient.email,
            },
            # Shown once to the doctor so it can be shared with the patient
            'temporary_password': temp_password,
            'email_sent': send_welcome_email(request, patient, temp_password),
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
        logger.warning('Health check: database unreachable: %s', e)
        db_error = str(e)

    return JsonResponse({
        'success': db_ok,
        'status': 'ok' if db_ok else 'error',
        'db_connected': db_ok,
        'db_error': db_error,
        'message': 'ReviveCare API is running' if db_ok else 'Database connection error',
        'authenticated': bool(request.session.get('patient_id'))
    }, status=200 if db_ok else 503)
