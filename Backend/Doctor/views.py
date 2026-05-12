from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Max, Min, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from Home.views import (VITAL_LIMITS, _initials, daily_charts, days_in_recovery, exercise_streak, goal_cards,
                        medication_adherence, notify_new_message, notify_patient, pain_by_day, vitals_by_day)
from Patients.models import Alert, Appointment, DoseTaken, Exercise, ExercisePlan, Message, Patient, RecoveryGoal, Vitals, Workout

from .forms import AppointmentForm, DoctorProfileForm, MedicationForm, PatientForm, RecoveryGoalForm
from .models import ClinicalNote, DoctorProfile


STATUSES = ['active', 'inactive', 'new']
PER_PAGE = 10
ADHERENCE_DAYS = 14


def _doctor(user):
    return f"Dr. {user.get_full_name() or user.username}"


def patient_rows(patients):
    """Patients with their latest workout, adherence (share of the last 14 days with a workout, counted from
    registration if that's more recent) and a status: active (worked out in the last 3 days), inactive or new."""
    done = Workout.objects.filter(patient__in=patients, total_reps__gt=0)
    spans = {p: (first, latest) for p, first, latest in
             done.values('patient').annotate(first=Min('date'), latest=Max('date')).values_list('patient', 'first', 'latest')}
    today = timezone.localdate()
    since = today - timedelta(days=ADHERENCE_DAYS - 1)
    active_days = dict(done.filter(date__gte=since).values('patient')
                       .annotate(days=Count('date', distinct=True)).values_list('patient', 'days'))
    rows = []
    for p in patients:
        first, latest = spans.get(p.id, (None, None))
        start = max(since, min(timezone.localdate(p.created_at), first or today))  # imported history can predate registration
        status = 'new' if not latest else 'active' if (today - latest).days <= 3 else 'inactive'
        ago = None if not latest else 'today' if latest == today else 'yesterday' if (today - latest).days == 1 else f"{(today - latest).days} days ago"
        rows.append({'id': p.id, 'name': p.name, 'initials': _initials(p.name), 'condition': p.condition or 'No condition recorded',
                     'status': status, 'last_workout': latest, 'last_workout_ago': ago,
                     'idle_days': (today - (latest or timezone.localdate(p.created_at))).days,
                     'adherence': round(100 * active_days.get(p.id, 0) / ((today - start).days + 1))})
    rows.sort(key=lambda r: r['last_workout'] or today.replace(year=1), reverse=True)
    return rows


def at_risk(rows, limit=5):
    """Patients who haven't worked out in more than 3 days (or since they were added), longest gap first."""
    return sorted((r for r in rows if r['idle_days'] > 3), key=lambda r: r['idle_days'], reverse=True)[:limit]


def recent_vitals(doctor, limit=5):
    """Each patient's latest reading from the last 7 days, out-of-range ones first."""
    latest = {}
    for v in Vitals.objects.filter(patient__in=Patient.for_doctor(doctor).filter(is_active=True),
                                   created_at__gte=timezone.now() - timedelta(days=7)).select_related('patient'):
        latest.setdefault(v.patient_id, v)  # newest first, so the first one seen is the latest
    rows = []
    for v in latest.values():
        bad = {f for f, _, _, low, high in VITAL_LIMITS if getattr(v, f) is not None and not low <= getattr(v, f) <= high}
        rows.append({'reading': v, 'bad_bp': bool(bad & {'systolic', 'diastolic'}), 'bad_hr': 'heart_rate' in bad,
                     'bad_temp': 'temperature' in bad, 'flagged': bool(bad)})
    return sorted(rows, key=lambda r: (not r['flagged'], -r['reading'].created_at.timestamp()))[:limit]


def dashboard_stats(doctor, rows):
    today = timezone.localdate()
    recent = Workout.objects.filter(patient__in=Patient.for_doctor(doctor), total_reps__gt=0)
    scores = [w.quality_score for w in recent.filter(date__gt=today - timedelta(days=14))]
    active = sum(r['status'] == 'active' for r in rows)
    return [
        {'icon': 'users', 'label': 'Active Patients', 'value': f"{active}/{len(rows)}", 'cls': 'bg-emerald-50 text-emerald-600'},
        {'icon': 'circle-alert', 'label': 'Need Attention', 'value': sum(r['status'] == 'inactive' for r in rows), 'cls': 'bg-rose-50 text-rose-600'},
        {'icon': 'trending-up', 'label': 'Avg Quality (14 days)', 'value': f"{round(sum(scores) / len(scores))}%" if scores else '—', 'cls': 'bg-blue-50 text-blue-600'},
        {'icon': 'dumbbell', 'label': 'Workouts This Week', 'value': recent.filter(date__gt=today - timedelta(days=7)).count(), 'cls': 'bg-amber-50 text-amber-600'},
    ]


@login_required
def doctor_dashboard(request):
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    patients = Patient.for_doctor(request.user).filter(is_active=True)
    everyone = patient_rows(patients)
    if q:
        patients = patients.filter(Q(name__icontains=q) | Q(email__icontains=q) | Q(condition__icontains=q))
    patients = patient_rows(patients)
    if status in STATUSES:
        patients = [p for p in patients if p['status'] == status]
    page = Paginator(patients, PER_PAGE).get_page(request.GET.get('page'))
    return render(request, 'doctor_dashboard.html', {
        'stats': dashboard_stats(request.user, everyone),
        'at_risk': at_risk(everyone),
        'recent_vitals': recent_vitals(request.user),
        'patients': page,
        'patient_count': len(patients),
        'page_query': urlencode({k: v for k, v in (('q', q), ('status', status)) if v}),
        'q': q, 'status': status if status in STATUSES else '', 'statuses': STATUSES,
    })


@login_required
def add_patient(request):
    return render(request, 'add_patient.html')


@login_required
def doctor_profile(request):
    user, profile = request.user, DoctorProfile.for_user(request.user)
    if request.method == 'POST':
        form = DoctorProfileForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            user.first_name, user.last_name, user.email = d['first_name'], d['last_name'], d['email']
            user.save(update_fields=['first_name', 'last_name', 'email'])
            profile.specialty, profile.phone = d['specialty'], d['phone']
            profile.save()
            messages.success(request, 'Profile saved.')
            return redirect('doctor_profile')
    else:
        form = DoctorProfileForm(initial={'first_name': user.first_name, 'last_name': user.last_name, 'email': user.email,
                                          'specialty': profile.specialty, 'phone': profile.phone})
    return render(request, 'doctor_profile.html', {'form': form})


@login_required
def edit_patient(request, patient_id):
    patient = get_object_or_404(Patient.for_doctor(request.user), id=patient_id)
    form = PatientForm(request.POST or None, instance=patient)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Patient details saved.')
        return redirect('patient_detail', patient_id=patient.id)
    return render(request, 'edit_patient.html', {'patient': patient, 'form': form})


@login_required
def add_note(request, patient_id):
    patient = get_object_or_404(Patient.for_doctor(request.user), id=patient_id)
    text = request.POST.get('text', '').strip()[:3000]
    if request.method == 'POST' and text:
        ClinicalNote.objects.create(patient=patient, author=request.user, text=text)
        messages.success(request, 'Note added.')
    return redirect(f"{reverse('patient_detail', args=[patient.id])}#notes")


@login_required
def set_patient_active(request, patient_id):
    """Deactivate a patient (hidden from the dashboard, can't sign in) or bring them back."""
    patient = get_object_or_404(Patient.for_doctor(request.user), id=patient_id)
    if request.method == 'POST':
        patient.is_active = request.POST.get('active') == '1'
        patient.save(update_fields=['is_active', 'updated_at'])
        messages.success(request, f"{patient.name} {'reactivated' if patient.is_active else 'deactivated'}.")
    return redirect('patient_detail', patient_id=patient.id)


@login_required
def alerts(request):
    """Serious chat messages from the doctor's patients; unread first."""
    mine = Alert.objects.filter(patient__in=Patient.for_doctor(request.user)).select_related('patient')
    if request.method == 'POST':
        mine.filter(id=request.POST.get('alert'), acknowledged_at=None).update(acknowledged_at=timezone.now(), acknowledged_by=request.user)
        return redirect('alerts')
    return render(request, 'alerts.html', {
        'unread': mine.filter(acknowledged_at=None),
        'read': mine.exclude(acknowledged_at=None).select_related('acknowledged_by')[:30],
    })


@login_required
def inbox(request, patient_id=None):
    """Patient message threads, latest first; with a patient, that thread plus a reply box."""
    mine = Patient.for_doctor(request.user)
    latest = {}
    for m in Message.objects.filter(patient__in=mine).select_related('patient').order_by('-created_at', '-id'):
        latest.setdefault(m.patient_id, m)
    unread = dict(Message.objects.filter(patient__in=mine, from_patient=True, read_at=None).values('patient')
                  .annotate(n=Count('id')).values_list('patient', 'n'))
    threads = [{'patient': m.patient, 'last': m, 'unread': unread.get(m.patient_id, 0)} for m in latest.values()]
    active = None
    if patient_id:
        active = get_object_or_404(mine, id=patient_id)
        if request.method == 'POST':
            body = request.POST.get('body', '').strip()[:2000]
            if body:
                notify_new_message(Message.objects.create(patient=active, from_patient=False, sender=request.user, body=body),
                                   request.build_absolute_uri('/')[:-1])
            return redirect(f"{reverse('inbox_thread', args=[active.id])}#latest")
        active.messages.filter(from_patient=True, read_at=None).update(read_at=timezone.now())
        for t in threads:
            if t['patient'].id == active.id:
                t['unread'] = 0
    return render(request, 'doctor_inbox.html', {'threads': threads, 'active': active,
                                                 'thread': active.messages.select_related('sender') if active else []})


@login_required
def calendar(request):
    """A week of the doctor's appointments, Monday to Sunday; ?week=YYYY-MM-DD picks the week containing that day."""
    try:
        day = datetime.strptime(request.GET.get('week', ''), '%Y-%m-%d').date()
    except ValueError:
        day = timezone.localdate()
    monday = day - timedelta(days=day.weekday())
    start = timezone.make_aware(datetime.combine(monday, datetime.min.time()))
    booked = Appointment.objects.filter(doctor=request.user, starts_at__gte=start, starts_at__lt=start + timedelta(days=7)) \
        .exclude(status='cancelled').select_related('patient')
    days = [{'date': monday + timedelta(days=i), 'appointments': []} for i in range(7)]
    for a in booked:
        days[(timezone.localdate(a.starts_at) - monday).days]['appointments'].append(a)
    return render(request, 'calendar.html', {
        'days': days, 'today': timezone.localdate(), 'count': len(booked),
        'prev': monday - timedelta(days=7), 'next': monday + timedelta(days=7), 'monday': monday, 'sunday': monday + timedelta(days=6),
    })


def _bounded(value, low, high):
    """An int within [low, high], or None (use the exercise default) for blank/invalid input."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if low <= number <= high else None


@login_required
def patient_plan(request, patient_id):
    """Choose which exercises a patient should do."""
    patient = get_object_or_404(Patient.for_doctor(request.user), id=patient_id)
    exercises = Exercise.objects.filter(is_active=True)
    if request.method == 'POST':
        chosen = set(request.POST.getlist('exercise'))
        for exercise in exercises:
            if str(exercise.id) in chosen:
                ExercisePlan.objects.update_or_create(patient=patient, exercise=exercise, defaults={
                    'is_active': True, 'assigned_by': request.user,
                    'target_reps': _bounded(request.POST.get(f'reps_{exercise.id}'), 1, 100),
                    'sets': _bounded(request.POST.get(f'sets_{exercise.id}'), 1, 10),
                })
            else:
                ExercisePlan.objects.filter(patient=patient, exercise=exercise).update(is_active=False)
        names = list(patient.plan.filter(is_active=True).values_list('exercise__name', flat=True))
        notify_patient(patient, 'Your exercise plan was updated',
                       f"{_doctor(request.user)} set your plan: {', '.join(names) or 'no exercises for now'}.",
                       '/patient/dashboard/', request.build_absolute_uri('/')[:-1])
        messages.success(request, f"Exercise plan saved for {patient.name}.")
        return redirect('patient_plan', patient_id=patient.id)
    assigned = {p.exercise_id: p for p in patient.plan.filter(is_active=True)}
    rows = [{'exercise': e, 'plan': assigned.get(e.id)} for e in exercises]
    return render(request, 'doctor_patient_plan.html', {'patient': patient, 'rows': rows})


@login_required
def patient_goals(request, patient_id):
    """Set measurable recovery goals for a patient."""
    patient = get_object_or_404(Patient.for_doctor(request.user), id=patient_id)
    if request.method == 'POST' and 'delete' in request.POST:
        patient.goals.filter(id=request.POST['delete']).delete()
        messages.success(request, 'Goal removed.')
        return redirect('patient_goals', patient_id=patient.id)
    form = RecoveryGoalForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        RecoveryGoal.objects.create(patient=patient, created_by=request.user, **form.cleaned_data)
        messages.success(request, 'Goal added.')
        return redirect('patient_goals', patient_id=patient.id)
    return render(request, 'doctor_patient_goals.html', {'patient': patient, 'form': form, 'goals': patient.goals.all()})


MISSED_GRACE = timedelta(hours=2)  # a dose counts as missed once it's this late


def missed_doses(patient, days=3):
    """Doses from the last `days` days that are over MISSED_GRACE late and weren't ticked off, newest first."""
    now = timezone.localtime()
    meds = list(patient.medications.filter(is_active=True))
    taken = set(DoseTaken.objects.filter(medication__in=meds, date__gte=now.date() - timedelta(days=days - 1))
                .values_list('medication_id', 'date', 'time'))
    missed = []
    for day in (now.date() - timedelta(days=i) for i in range(days)):
        for m in meds:
            for t in m.due_on(day):
                due = timezone.make_aware(datetime.combine(day, datetime.strptime(t, '%H:%M').time()))
                if due + MISSED_GRACE < now and (m.id, day, t) not in taken:
                    missed.append({'med': m, 'when': due})
    return sorted(missed, key=lambda d: d['when'], reverse=True)


@login_required
def patient_medications(request, patient_id):
    """Prescribe medicines with a daily schedule, or stop them."""
    patient = get_object_or_404(Patient.for_doctor(request.user), id=patient_id)
    if request.method == 'POST' and 'stop' in request.POST:
        patient.medications.filter(id=request.POST['stop']).update(is_active=False, end_date=timezone.localdate())
        messages.success(request, 'Medication stopped.')
        return redirect('patient_medications', patient_id=patient.id)
    form = MedicationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.instance.patient, form.instance.prescribed_by = patient, request.user
        form.save()
        messages.success(request, f"{form.instance.name} added.")
        return redirect('patient_medications', patient_id=patient.id)
    return render(request, 'doctor_patient_medications.html', {
        'patient': patient, 'form': form,
        'current': patient.medications.filter(is_active=True), 'stopped': patient.medications.filter(is_active=False)[:10],
    })


@login_required
def patient_appointments(request, patient_id):
    """Book an appointment for a patient (POST from the patient page), or cancel one."""
    patient = get_object_or_404(Patient.for_doctor(request.user), id=patient_id)
    if request.method != 'POST':
        return redirect('patient_detail', patient_id=patient.id)
    site = request.build_absolute_uri('/')[:-1]
    if 'cancel' in request.POST:
        appointment = patient.appointments.filter(id=request.POST['cancel'], status='scheduled').first()
        if appointment:
            appointment.status = 'cancelled'
            appointment.save(update_fields=['status'])
            notify_patient(patient, 'Appointment cancelled',
                           f"{_doctor(request.user)} cancelled your appointment on {timezone.localtime(appointment.starts_at):%a %d %b, %H:%M}.",
                           '/patient/dashboard/#appointment', site)
        messages.success(request, 'Appointment cancelled.')
        return redirect(f"{reverse('patient_detail', args=[patient.id])}#appointments")
    form = AppointmentForm(request.POST, doctor=request.user)
    if form.is_valid():
        form.instance.patient, form.instance.doctor = patient, request.user
        form.save()
        a = form.instance
        notify_patient(patient, 'Appointment booked',
                       f"{_doctor(request.user)} booked {a.reason or 'an appointment'} for {timezone.localtime(a.starts_at):%a %d %b, %H:%M}"
                       + (f" at {a.location}" if a.location else '') + ('. It is a video call.' if a.meeting_url else '.'),
                       '/patient/dashboard/#appointment', site)
        messages.success(request, f"Appointment booked for {timezone.localtime(form.instance.starts_at):%a %d %b, %H:%M}.")
        return redirect(f"{reverse('patient_detail', args=[patient.id])}#appointments")
    return patient_detail(request, patient_id, appointment_form=form)


@login_required
def patient_report(request, patient_id):
    """A one-page summary of the last 30 days to print or save as PDF."""
    patient = get_object_or_404(Patient.for_doctor(request.user), id=patient_id)
    today = timezone.localdate()
    since = today - timedelta(days=29)
    names = dict(Exercise.objects.values_list('slug', 'name'))
    by_exercise = {}
    for w in Workout.objects.filter(patient=patient, total_reps__gt=0, date__gte=since):
        row = by_exercise.setdefault(w.exercise, {'name': names.get(w.exercise, w.exercise), 'sessions': 0, 'reps': 0, 'scores': []})
        row['sessions'] += 1
        row['reps'] += w.total_reps
        row['scores'].append(w.quality_score)
    exercises = sorted(({**r, 'quality': round(sum(r['scores']) / len(r['scores']))} for r in by_exercise.values()),
                       key=lambda r: -r['sessions'])
    pain = pain_by_day(patient, 28)
    pain_weeks = []
    for i in range(0, 28, 7):
        scores = [d['pain'] for d in pain[i:i + 7] if d['pain'] is not None]
        pain_weeks.append({'start': pain[i]['date'], 'end': pain[i + 6]['date'],
                           'avg': round(sum(scores) / len(scores), 1) if scores else None})
    return render(request, 'patient_report.html', {
        'patient': patient, 'today': today, 'since': since, 'doctor': _doctor(request.user),
        'stats': [
            ('Days in recovery', days_in_recovery(patient)),
            ('Sessions', sum(r['sessions'] for r in exercises)),
            ('Total reps', sum(r['reps'] for r in exercises)),
            ('Current streak', f"{exercise_streak(patient)} days"),
        ],
        'exercises': exercises,
        'plan': patient.plan.filter(is_active=True).select_related('exercise'),
        'goals': goal_cards(patient),
        'pain_weeks': pain_weeks,
        'vitals': patient.vitals.filter(created_at__date__gte=since)[:10],
        'medications': [(m, medication_adherence(m, 30)) for m in patient.medications.filter(is_active=True)],
        'notes': patient.notes.select_related('author')[:5],
    })


@login_required
def patient_detail(request, patient_id, appointment_form=None):
    """Everything a doctor needs about one patient on a single page."""
    patient = get_object_or_404(Patient.for_doctor(request.user), id=patient_id)
    today = timezone.localdate()
    workouts = Workout.objects.filter(patient=patient, total_reps__gt=0)
    recent = workouts.filter(date__gt=today - timedelta(days=30))
    scores = [w.quality_score for w in recent]
    names = dict(Exercise.objects.values_list('slug', 'name'))
    since = today - timedelta(days=29)
    return render(request, 'patient_detail.html', {
        **daily_charts(workouts.filter(date__gte=since), [since + timedelta(days=i) for i in range(30)]),
        'days': 30,
        'patient': patient,
        'initials': _initials(patient.name),
        'stats': [
            {'label': 'Days in recovery', 'value': days_in_recovery(patient)},
            {'label': 'Current streak', 'value': f"{exercise_streak(patient)} days"},
            {'label': 'Sessions (30 days)', 'value': recent.count()},
            {'label': 'Avg quality (30 days)', 'value': f"{round(sum(scores) / len(scores))}%" if scores else '—'},
        ],
        'plan': patient.plan.filter(is_active=True).select_related('exercise'),
        'goals': goal_cards(patient),
        'medications': [(m, medication_adherence(m)) for m in patient.medications.filter(is_active=True)],
        'missed_doses': missed_doses(patient),
        'appointment_form': appointment_form or AppointmentForm(doctor=request.user),
        'appointments': patient.appointments.filter(status='scheduled', starts_at__gte=timezone.now() - timedelta(hours=1)),
        'pain_chart': [{'label': d['date'].strftime('%d %b'), 'value': d['pain']} for d in pain_by_day(patient, 30)],
        'diary': patient.diary.all()[:5],
        'vitals_chart': vitals_by_day(patient, 30),
        'latest_vitals': patient.vitals.first(),
        'notes': patient.notes.select_related('author'),
        'chat': patient.chat_messages.order_by('-created_at', '-id')[:30],  # newest first; the template stacks them bottom-up
        'sessions': [{'date': w.date, 'name': names.get(w.exercise, w.exercise), 'reps': w.total_reps, 'target': w.target_reps,
                      'score': round(w.quality_score), 'completed': w.completed}
                     for w in workouts.order_by('-date', '-created_at')[:10]],
    })
