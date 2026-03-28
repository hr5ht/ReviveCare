from datetime import timedelta

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from Patients.models import DoseTaken, Medication


class Command(BaseCommand):
    help = 'Email each patient the doses due in the next hour that they have not ticked off. Run hourly, e.g. cron "0 * * * *".'

    def add_arguments(self, parser):
        parser.add_argument('--minutes', type=int, default=60, help='How far ahead to look (match the cron interval)')

    def handle(self, minutes, **options):
        now = timezone.localtime()
        start, end = now.strftime('%H:%M'), (now + timedelta(minutes=minutes)).strftime('%H:%M')
        in_window = (lambda t: start <= t < end) if start < end else (lambda t: t >= start or t < end)  # window crossing midnight
        today = now.date()
        taken = set(DoseTaken.objects.filter(date=today).values_list('medication_id', 'time'))
        due = {}  # patient -> [(time, medication)]
        meds = Medication.objects.filter(is_active=True, patient__is_active=True).select_related('patient')
        for med in meds:
            for t in med.due_on(today):
                if in_window(t) and (med.id, t) not in taken:
                    due.setdefault(med.patient, []).append((t, med))
        sent = 0
        for patient, doses in due.items():
            lines = '\n'.join(f"  {t}  {m}" + (f" ({m.instructions})" if m.instructions else '') for t, m in sorted(doses, key=lambda d: d[0]))
            try:
                send_mail('Medicine reminder · ReViveCare',
                          f"Hi {patient.name},\n\nIt's nearly time for:\n{lines}\n\n"
                          "Tick each dose off on your ReViveCare dashboard once you've taken it.\n", None, [patient.email])
                sent += 1
            except Exception as e:  # one bad address shouldn't stop the rest
                self.stderr.write(f"Reminder for patient {patient.id} failed: {e}")
        self.stdout.write(f"Sent {sent} reminder email(s) for {sum(len(d) for d in due.values())} dose(s).")
