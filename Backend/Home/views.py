import logging
from datetime import timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import models
from django.shortcuts import render, redirect
from django.utils import timezone
from Patients.goals import LOWER_IS_BETTER, progress
from Patients.models import Exercise, Patient, Workout

from .forms import PatientContactForm

logger = logging.getLogger(__name__)


def patient_page(view):
    """Sign out deactivated patients; send those still on a temporary password to the change-password page first."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        patient = _logged_in_patient(request)
        if patient and not patient.is_active:
            request.session.flush()
            return redirect('patient_login')
        if patient and patient.must_change_password:
            return redirect('change_password')
        return view(request, *args, **kwargs)
    return wrapper


def _initials(name):
    return ''.join(n[0] for n in name.split())


def home(request):
    return render(request, 'home.html', {
        'features': [
            {'icon': 'clock', 'title': 'Real-Time Monitoring', 'description': 'Track patient recovery progress with continuous health data monitoring and automated alerts.'},
            {'icon': 'heart', 'title': 'Personalized Care Plans', 'description': "Customized recovery protocols tailored to each patient's specific medical needs and conditions."},
            {'icon': 'shield', 'title': 'HIPAA Compliant', 'description': 'Enterprise-grade security ensuring patient data privacy and regulatory compliance.'},
            {'icon': 'trending-up', 'title': 'Analytics Dashboard', 'description': 'Comprehensive insights into recovery trends, medication adherence, and health outcomes.'},
        ],
        'benefits': [
            'Reduce hospital readmission rates',
            'Improve patient satisfaction scores',
            'Streamline post-discharge communication',
            'Enable proactive intervention',
            'Comprehensive medication management',
            'Integrated telehealth consultations',
        ],
    })


def patient_login(request):
    return render(request, 'patient_login.html')


def days_in_recovery(patient):
    """Days since surgery/discharge, or a dash when the doctor hasn't set the date."""
    if not patient.surgery_date:
        return '—'
    return str(max(0, (timezone.localdate() - patient.surgery_date).days))


def todays_tasks(request):
    """One task per assigned exercise, ticked off once today's workout for it is complete."""
    patient = _logged_in_patient(request)
    today = {}  # exercise slug -> (completed, reps done today)
    for w in Workout.objects.filter(patient=patient, date=timezone.localdate()):
        done, reps = today.get(w.exercise, (False, 0))
        today[w.exercise] = (done or w.completed, reps + w.total_reps)
    tasks = []
    for e, p in exercises_for(request):
        if not p:
            continue
        done, reps = today.get(e.slug, (False, 0))
        total = p.total_sets * p.reps
        detail = f"{p.total_sets} × {p.reps} reps" if done or not reps else f"{min(reps, total)}/{total} reps today"
        tasks.append({'name': e.name, 'detail': detail, 'icon': e.icon, 'url': f'/patient/exercises/{e.slug}/', 'completed': done})
    return tasks


def progress_score(patient, days=14):
    """Average rep-quality score (0-100) over recent workouts, or a dash with no data yet."""
    since = timezone.localdate() - timedelta(days=days - 1)
    scores = [w.quality_score for w in Workout.objects.filter(patient=patient, date__gte=since, total_reps__gt=0)]
    return f"{round(sum(scores) / len(scores))}%" if scores else '—'


def exercise_streak(patient):
    """Consecutive days with a workout, ending today (or yesterday, so the streak survives until today's session)."""
    days = set(Workout.objects.filter(patient=patient, total_reps__gt=0).values_list('date', flat=True))
    day = timezone.localdate()
    if day not in days:
        day -= timedelta(days=1)
    streak = 0
    while day in days:
        streak += 1
        day -= timedelta(days=1)
    return streak


def weekly_summary(patient):
    """Last 7 days vs the 7 before: reps (with % change), active days and average quality."""
    today = timezone.localdate()
    this_week = Workout.objects.filter(patient=patient, date__gt=today - timedelta(days=7), total_reps__gt=0)
    last_week = Workout.objects.filter(patient=patient, date__gt=today - timedelta(days=14), date__lte=today - timedelta(days=7))
    reps, prev = sum(w.total_reps for w in this_week), sum(w.total_reps for w in last_week)
    scores = [w.quality_score for w in this_week]
    return {
        'reps': reps,
        'change': round((reps - prev) / prev * 100) if prev else None,
        'active_days': this_week.values('date').distinct().count(),
        'quality': round(sum(scores) / len(scores)) if scores else None,
    }


def best_streak(patient):
    days = sorted(set(Workout.objects.filter(patient=patient, total_reps__gt=0).values_list('date', flat=True)))
    best = run = 0
    for i, day in enumerate(days):
        run = run + 1 if i and (day - days[i - 1]).days == 1 else 1
        best = max(best, run)
    return best


def achievements(patient, tasks):
    """Badges derived from workout history (nothing stored, so they can't drift from the data)."""
    workouts = Workout.objects.filter(patient=patient, total_reps__gt=0)
    total_reps = sum(workouts.values_list('total_reps', flat=True))
    streak = best_streak(patient)
    perfect = workouts.filter(total_reps__gte=10).filter(excellent_reps=models.F('total_reps')).exists()
    return [
        {'name': 'First workout', 'how': 'Finish any exercise session', 'icon': 'play', 'earned': workouts.exists()},
        {'name': '3-day streak', 'how': 'Exercise 3 days in a row', 'icon': 'flame', 'earned': streak >= 3},
        {'name': '7-day streak', 'how': 'Exercise 7 days in a row', 'icon': 'flame', 'earned': streak >= 7},
        {'name': '100 reps', 'how': 'Reach 100 reps in total', 'icon': 'dumbbell', 'earned': total_reps >= 100},
        {'name': '500 reps', 'how': 'Reach 500 reps in total', 'icon': 'trophy', 'earned': total_reps >= 500},
        {'name': 'Perfect session', 'how': '10+ reps, every one excellent', 'icon': 'star', 'earned': perfect},
        {'name': 'Full day', 'how': "Complete every task in today's plan", 'icon': 'circle-check',
         'earned': bool(tasks) and all(t['completed'] for t in tasks)},
    ]


def workouts_this_week(patient):
    """Days in the last 7 with at least one workout session."""
    since = timezone.localdate() - timedelta(days=6)
    return Workout.objects.filter(patient=patient, date__gte=since, total_reps__gt=0).values('date').distinct().count()


def goal_cards(patient):
    cards = []
    for goal in patient.goals.select_related('exercise'):
        current, percent, achieved = progress(goal)
        cards.append({'text': goal.describe(), 'percent': 100 if goal.achieved_at else percent,
                      'achieved': bool(goal.achieved_at) or achieved, 'current': current, 'due': goal.due_date})
    return cards


@patient_page
def patient_dashboard(request):
    patient = Patient.objects.filter(id=request.session.get('patient_id')).first()
    if not patient:
        return render(request, 'patient_dashboard.html', {'patient': None})
    tasks = todays_tasks(request)
    badges = achievements(patient, tasks)
    goals = goal_cards(patient)
    return render(request, 'patient_dashboard.html', {
        'goals': goals,
        'patient': patient,
        'week': weekly_summary(patient),
        'badges': badges,
        'badges_earned': sum(b['earned'] for b in badges),
        'initials': _initials(patient.name or 'Patient'),
        'tasks': tasks,
        'tasks_done': sum(t['completed'] for t in tasks),
        'recovery_stats': [
            {'label': 'Days in Recovery', 'value': days_in_recovery(patient), 'icon': 'calendar', 'cls': 'bg-emerald-100 text-emerald-600'},
            {'label': 'Progress Score', 'value': progress_score(patient), 'icon': 'trending-up', 'cls': 'bg-blue-100 text-blue-600'},
            {'label': 'Workouts This Week', 'value': str(workouts_this_week(patient)), 'icon': 'dumbbell', 'cls': 'bg-purple-100 text-purple-600'},
            {'label': 'Exercise Streak', 'value': f"{exercise_streak(patient)} days", 'icon': 'flame', 'cls': 'bg-orange-100 text-orange-600'},
            {'label': 'Goals Achieved', 'value': f"{sum(g['achieved'] for g in goals)}/{len(goals)}" if goals else '—', 'icon': 'target', 'cls': 'bg-purple-100 text-purple-600'},
        ],
    })


def _logged_in_patient(request):
    return Patient.objects.filter(id=request.session.get('patient_id')).first()


@patient_page
def patient_profile(request):
    patient = _logged_in_patient(request)
    if not patient:
        return redirect('patient_login')
    fields = ['phone', 'emergency_contact_name', 'emergency_contact_phone']
    if request.method == 'POST':
        form = PatientContactForm(request.POST)
        if form.is_valid():
            for f in fields:
                setattr(patient, f, form.cleaned_data[f])
            patient.save(update_fields=fields)
            messages.success(request, 'Contact details saved.')
            return redirect('patient_profile')
    else:
        form = PatientContactForm(initial={f: getattr(patient, f) for f in fields})
    return render(request, 'patient_profile.html', {'patient': patient, 'initials': _initials(patient.name), 'form': form})


def change_password(request):
    patient = Patient.objects.filter(id=request.session.get('patient_id')).first()
    if not patient:
        return redirect('patient_login')
    return render(request, 'change_password.html', {'patient': patient, 'fields': [
        ('current', 'Current Password', 'Enter your current password'),
        ('new_password', 'New Password', 'At least 8 characters'),
        ('confirm', 'Confirm New Password', 'Re-enter the new password'),
    ]})


def exercises_for(request):
    """(exercise, plan) pairs a patient should see: their active plan, or the whole library if they have none."""
    patient = _logged_in_patient(request)
    plan = list(patient.plan.filter(is_active=True, exercise__is_active=True).select_related('exercise')) if patient else []
    if plan:
        return [(p.exercise, p) for p in plan]
    return [(e, None) for e in Exercise.objects.filter(is_active=True)]


def _find_exercise(request, slug):
    return next(((e, p) for e, p in exercises_for(request) if e.slug == slug), (None, None))


def daily_charts(workouts, day_list):
    """Per-day reps and rep-quality series for the history charts (shared with the doctor's patient page)."""
    reps, quality = {}, {}
    for w in workouts:
        reps[w.date] = reps.get(w.date, 0) + w.total_reps
        q = quality.setdefault(w.date, [0, 0, 0])
        q[0] += w.excellent_reps; q[1] += w.good_reps; q[2] += w.partial_reps
    return {
        'reps_chart': [{'label': d.strftime('%d %b'), 'value': reps.get(d, 0)} for d in day_list],
        'reps_total': sum(reps.values()),
        'quality_chart': [{'label': d.strftime('%d %b'), 'parts': quality.get(d, [0, 0, 0])} for d in day_list],
        'quality_totals': [sum(q[i] for q in quality.values()) for i in range(3)],
    }


HISTORY_RANGES = [7, 30, 90]


@patient_page
def workout_history(request):
    patient = _logged_in_patient(request)
    if not patient:
        return redirect('patient_login')
    days = int(request.GET.get('days', 30)) if request.GET.get('days', '30').isdigit() else 30
    days = days if days in HISTORY_RANGES else 30
    since = timezone.localdate() - timedelta(days=days - 1)
    workouts = Workout.objects.filter(patient=patient, date__gte=since, total_reps__gt=0)
    names = dict(Exercise.objects.values_list('slug', 'name'))
    done_slugs = sorted(set(Workout.objects.filter(patient=patient).values_list('exercise', flat=True)), key=lambda s: names.get(s, s))
    exercise = request.GET.get('exercise', '')
    if exercise in done_slugs:
        workouts = workouts.filter(exercise=exercise)
    else:
        exercise = ''
    sessions = [{'date': w.date, 'name': names.get(w.exercise, w.exercise), 'reps': w.total_reps, 'target': w.target_reps,
                 'score': round(w.quality_score), 'duration': f"{w.duration_seconds // 60}:{w.duration_seconds % 60:02d}",
                 'completed': w.completed} for w in workouts.order_by('-date', '-created_at')]
    day_list = [since + timedelta(days=i) for i in range(days)]
    charts = daily_charts(workouts, day_list)

    # Range of motion: best rep angle per day for one exercise (the selected one, else the most practised)
    rom_slug = exercise or max(done_slugs, key=lambda s: workouts.filter(exercise=s).count(), default='')
    rom_exercise = Exercise.objects.filter(slug=rom_slug).first()
    lower_is_better = bool(rom_exercise and rom_exercise.rule in LOWER_IS_BETTER)
    best_by_day = {}
    for w in workouts.filter(exercise=rom_slug):
        angles = [a['angle'] for a in w.angles_data if isinstance(a, dict) and a.get('angle')]
        if angles:
            best = min(angles) if lower_is_better else max(angles)
            prev = best_by_day.get(w.date)
            best_by_day[w.date] = best if prev is None else (min(prev, best) if lower_is_better else max(prev, best))
    rom_chart = [{'label': d.strftime('%d %b'), 'value': best_by_day.get(d)} for d in day_list]

    return render(request, 'workout_history.html', {
        'patient': patient, 'initials': _initials(patient.name), 'sessions': sessions, 'days': days, 'ranges': HISTORY_RANGES,
        **charts,
        'rom_chart': rom_chart, 'rom_has_data': bool(best_by_day), 'rom_exercise': rom_exercise, 'rom_lower_is_better': lower_is_better,
        'rom_unit': '%' if rom_exercise and rom_exercise.rule == 'heel' else '°',

        'exercise': exercise, 'exercise_options': [(s, names.get(s, s)) for s in done_slugs],
    })


@patient_page
def exercises(request):
    return render(request, 'exercises.html', {'exercises': [e.to_dict(p) for e, p in exercises_for(request)]})


@patient_page
def exercise_detail(request, slug):
    exercise, plan = _find_exercise(request, slug)
    if not exercise:
        return redirect('exercises')
    return render(request, 'exercise_detail.html', {'exercise': exercise.to_dict(plan)})


@patient_page
def exercise_workout(request, exercise_id):
    exercise, plan = _find_exercise(request, exercise_id)
    if not exercise:
        return redirect('exercises')
    return render(request, 'exercise_workout.html', {'exercise': exercise.to_dict(plan)})


@patient_page
def chat(request):
    return render(request, 'chat.html')


RESET_SALT = 'patient-password-reset'
RESET_MAX_AGE = 24 * 60 * 60  # seconds


def _reset_token(patient):
    # Includes a slice of the current password hash, so the link stops working once the password changes
    return signing.dumps({'id': patient.id, 'h': patient.password[-16:]}, salt=RESET_SALT)


def _patient_from_token(token):
    try:
        data = signing.loads(token, salt=RESET_SALT, max_age=RESET_MAX_AGE)
    except signing.BadSignature:
        return None
    patient = Patient.objects.filter(id=data.get('id')).first()
    return patient if patient and patient.password[-16:] == data.get('h') else None


def patient_forgot_password(request):
    sent = False
    if request.method == 'POST':
        patient = Patient.objects.filter(email=request.POST.get('email', '').strip().lower(), is_active=True).first()
        if patient:
            link = request.build_absolute_uri(f'/patient/reset-password/{_reset_token(patient)}/')
            try:
                send_mail('Reset your ReViveCare password',
                          f"Hi {patient.name},\n\nChoose a new ReViveCare password here (the link expires in 24 hours):\n\n"
                          f"{link}\n\nIf you didn't ask for this, you can ignore this email.\n\n— The ReViveCare team",
                          None, [patient.email])
            except Exception:
                logger.exception('Patient reset email failed for %s', patient.id)
        sent = True  # same response either way, so the page doesn't reveal which emails exist
    return render(request, 'patient_forgot_password.html', {'sent': sent})


def patient_reset_password(request, token):
    patient = _patient_from_token(token)
    error = None
    if patient and request.method == 'POST':
        new, confirm = request.POST.get('new_password', ''), request.POST.get('confirm', '')
        try:
            if new != confirm:
                raise ValidationError("The passwords don't match.")
            validate_password(new)
        except ValidationError as e:
            error = ' '.join(e.messages)
        else:
            patient.password = make_password(new)
            patient.must_change_password = False
            patient.failed_login_count, patient.locked_until = 0, None
            patient.save(update_fields=['password', 'must_change_password', 'failed_login_count', 'locked_until'])
            return render(request, 'patient_reset_password.html', {'done': True})
    return render(request, 'patient_reset_password.html', {'valid': bool(patient), 'error': error})
