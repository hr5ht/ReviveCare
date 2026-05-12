from datetime import timedelta

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from Patients.models import Appointment


class Command(BaseCommand):
    help = 'Email patients about appointments starting about a day from now. Run hourly, e.g. cron "0 * * * *".'

    def add_arguments(self, parser):
        parser.add_argument('--hours', type=int, default=24, help='How long before the appointment to remind')
        parser.add_argument('--minutes', type=int, default=60, help='Window width (match the cron interval)')

    def handle(self, hours, minutes, **options):
        # Each run covers the next slice of time, so every appointment falls in exactly one run's window.
        start = timezone.now() + timedelta(hours=hours)
        due = Appointment.objects.filter(status='scheduled', patient__is_active=True, patient__email_reminders=True,
                                         starts_at__gte=start,
                                         starts_at__lt=start + timedelta(minutes=minutes)).select_related('patient', 'doctor')
        sent = 0
        for a in due:
            when = timezone.localtime(a.starts_at)
            details = [f"  When:  {when:%A %d %B, %H:%M} ({a.duration_minutes} min)"]
            if a.doctor:
                details.append(f"  With:  Dr. {a.doctor.get_full_name() or a.doctor.username}")
            if a.location:
                details.append(f"  Where: {a.location}")
            if a.meeting_url:
                details.append(f"  Video: {a.meeting_url}")
            try:
                send_mail('Appointment reminder · ReViveCare',
                          f"Hi {a.patient.name},\n\nA reminder about your {a.reason or 'appointment'}:\n" + '\n'.join(details) +
                          "\n\nCan't make it? Ask to reschedule from your ReViveCare dashboard.\n", None, [a.patient.email])
                sent += 1
            except Exception as e:  # one bad address shouldn't stop the rest
                self.stderr.write(f"Reminder for appointment {a.id} failed: {e}")
        self.stdout.write(f"Sent {sent} appointment reminder(s).")
