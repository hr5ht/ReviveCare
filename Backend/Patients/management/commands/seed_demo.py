import random
from datetime import datetime, time, timedelta

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from Doctor.models import DoctorProfile
from Patients.models import (Appointment, DiaryEntry, DoseTaken, Exercise, ExercisePlan, Medication, Message, Notification,
                             Patient, RecoveryGoal, Vitals, Workout)

DOCTOR = ('doctor', 'Doctor-demo-2026')
PATIENT = ('demo@revivecare.com', 'demo1234')


class Command(BaseCommand):
    help = ('Create a demo doctor and a demo patient with 30 days of workouts, pain, vitals, medicines, messages '
            f'and an appointment. Sign in as {DOCTOR[0]} / {DOCTOR[1]} or {PATIENT[0]} / {PATIENT[1]}. Safe to re-run.')

    def add_arguments(self, parser):
        parser.add_argument('--allow-production', action='store_true',
                            help='Run even with DEBUG off. The demo accounts have published passwords.')

    def handle(self, allow_production, **options):
        if not settings.DEBUG and not allow_production:
            raise CommandError('DEBUG is off. The demo accounts have known passwords; pass --allow-production if you mean it.')
        rng = random.Random(42)  # same data every run
        now, today = timezone.now(), timezone.localdate()

        doctor, _ = User.objects.update_or_create(username=DOCTOR[0], defaults={
            'first_name': 'Meera', 'last_name': 'Anderson', 'email': 'doctor@example.com', 'is_active': True})
        doctor.set_password(DOCTOR[1])
        doctor.save()
        DoctorProfile.objects.update_or_create(user=doctor, defaults={'specialty': 'Orthopedic Surgeon', 'phone': '+91 98765 00000'})

        Patient.objects.filter(email=PATIENT[0]).delete()  # start clean; cascades to all of their records
        patient = Patient.objects.create(
            name='Demo Patient', email=PATIENT[0], password=make_password(PATIENT[1]), doctor=doctor,
            info='Right total knee replacement. Walking with a stick, building quad strength and range of motion.',
            condition='Total knee replacement (right)', surgery_date=today - timedelta(days=36),
            phone='+91 91234 56789', emergency_contact_name='Ravi (son)', emergency_contact_phone='+91 99887 76655',
            created_at=now - timedelta(days=32))

        exercises = list(Exercise.objects.filter(is_active=True).order_by('order')[:3])
        for e in exercises:
            ExercisePlan.objects.create(patient=patient, exercise=e, assigned_by=doctor)

        # 30 days of workouts on most days, improving quality as recovery goes on
        workouts = 0
        for days_ago in range(29, -1, -1):
            if rng.random() < 0.3 and days_ago:
                continue
            for e in rng.sample(exercises, k=rng.randint(1, len(exercises))):
                reps = rng.randint(8, e.target_reps + 4)
                skill = 0.4 + 0.5 * (29 - days_ago) / 29
                excellent = round(reps * skill * rng.uniform(0.7, 1))
                good = round((reps - excellent) * 0.7)
                Workout.objects.create(patient=patient, exercise=e.slug, date=today - timedelta(days=days_ago),
                                       total_reps=reps, target_reps=e.target_reps, excellent_reps=excellent, good_reps=good,
                                       partial_reps=reps - excellent - good, duration_seconds=reps * rng.randint(4, 7),
                                       completed=reps >= e.target_reps)
                workouts += 1

        # Pain easing from about 7 to about 3, logged most evenings; vitals every other day
        for days_ago in range(27, -1, -1):
            when = timezone.make_aware(datetime.combine(today - timedelta(days=days_ago), time(20, rng.randint(0, 59))))
            if rng.random() < 0.8:
                pain = max(0, min(10, round(7 - 4 * (27 - days_ago) / 27 + rng.uniform(-1, 1))))
                entry = DiaryEntry.objects.create(patient=patient, pain=pain, notes='' if rng.random() < 0.7 else 'Stiff after the stairs.',
                                                  symptoms=rng.sample(['swelling', 'stiffness', 'fatigue', 'poor_sleep'], k=rng.randint(0, 2)))
                DiaryEntry.objects.filter(id=entry.id).update(created_at=when)
            if days_ago % 2 == 0:
                v = Vitals.objects.create(patient=patient, systolic=rng.randint(118, 136), diastolic=rng.randint(76, 86),
                                          heart_rate=rng.randint(66, 84), temperature=round(rng.uniform(97.9, 99.3), 1))
                Vitals.objects.filter(id=v.id).update(created_at=when - timedelta(hours=12))

        paracetamol = Medication.objects.create(patient=patient, name='Paracetamol', dose='500 mg, 1 tablet', times=['08:00', '20:00'],
                                                instructions='after food', start_date=today - timedelta(days=20), prescribed_by=doctor)
        aspirin = Medication.objects.create(patient=patient, name='Aspirin', dose='75 mg', times=['09:00'], start_date=today - timedelta(days=20),
                                            end_date=today + timedelta(days=14), prescribed_by=doctor)
        for days_ago in range(1, 15):
            day = today - timedelta(days=days_ago)
            for med in (paracetamol, aspirin):
                for t in med.due_on(day):
                    if rng.random() < 0.85:
                        DoseTaken.objects.create(medication=med, date=day, time=t)

        RecoveryGoal.objects.create(patient=patient, kind='sessions', target=30, created_by=doctor, due_date=today + timedelta(days=14))
        RecoveryGoal.objects.create(patient=patient, kind='streak', target=3, created_by=doctor)
        RecoveryGoal.objects.create(patient=patient, kind='total_reps', target=1000, created_by=doctor, due_date=today + timedelta(days=30))

        Appointment.objects.create(patient=patient, doctor=doctor, starts_at=timezone.make_aware(datetime.combine(today + timedelta(days=3), time(11))),
                                   reason='2-week follow-up', location='Clinic room 2')
        Message.objects.create(patient=patient, from_patient=True, body='The knee is less swollen this week. Is it OK to walk without the stick at home?',
                               read_at=now - timedelta(days=1, hours=20))
        Message.objects.create(patient=patient, from_patient=False, sender=doctor,
                               body='Good progress! Yes, short walks at home without the stick are fine. Keep it for outdoors for one more week.')
        Notification.objects.create(patient=patient, title='Appointment booked', body='2-week follow-up, 3 days from now.', link='/patient/dashboard/#appointment')

        self.stdout.write(self.style.SUCCESS(
            f"Demo ready: {workouts} workouts over 30 days.\n"
            f"  Doctor:  {DOCTOR[0]} / {DOCTOR[1]}  (/doctor/login/)\n"
            f"  Patient: {PATIENT[0]} / {PATIENT[1]}  (/patient/login/)"))
