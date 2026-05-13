from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from Doctor.views import at_risk, patient_rows
from Patients.models import Alert, Appointment, Message, Patient


class Command(BaseCommand):
    help = 'Email each doctor a weekly round-up of their patients. Run weekly, e.g. cron "0 8 * * 1" (Mondays 08:00).'

    def handle(self, **options):
        sent = 0
        now = timezone.now()
        for doctor in User.objects.filter(is_active=True, patients__is_active=True).exclude(email='').distinct():
            patients = Patient.objects.filter(doctor=doctor, is_active=True)
            rows = patient_rows(patients)
            alerts = Alert.objects.filter(patient__in=patients, acknowledged_at=None).count()
            unread = Message.objects.filter(patient__in=patients, from_patient=True, read_at=None).count()
            upcoming = Appointment.objects.filter(doctor=doctor, status='scheduled', starts_at__gte=now,
                                                  starts_at__lt=now + timedelta(days=7)).select_related('patient')
            lines = [f"  Patients:            {len(rows)} ({sum(r['status'] == 'active' for r in rows)} active this week)",
                     f"  Open alerts:         {alerts}",
                     f"  Unread messages:     {unread}",
                     f"  Appointments ahead:  {len(upcoming)}"]
            risk = at_risk(rows)
            if risk:
                lines += ['', 'Not exercising lately:'] + [f"  {r['name']}: {r['idle_days']} days" for r in risk]
            if upcoming:
                lines += ['', 'This week:'] + [f"  {timezone.localtime(a.starts_at):%a %d %b %H:%M}  {a.patient.name}" for a in upcoming]
            try:
                send_mail('Your weekly patient digest · ReViveCare',
                          f"Hi Dr. {doctor.get_full_name() or doctor.username},\n\n" + '\n'.join(lines) +
                          f"\n\nOpen your dashboard: {settings.SITE_URL}/doctor/dashboard/\n", None, [doctor.email])
                sent += 1
            except Exception as e:  # one bad address shouldn't stop the rest
                self.stderr.write(f"Digest for doctor {doctor.id} failed: {e}")
        self.stdout.write(f"Sent {sent} doctor digest(s).")
