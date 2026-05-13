from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

from Home.views import exercise_streak, pain_trend, weekly_summary
from Patients.models import Patient


class Command(BaseCommand):
    help = 'Email each patient a summary of their last 7 days. Run weekly, e.g. cron "0 9 * * 1" (Mondays 09:00).'

    def handle(self, **options):
        sent = 0
        for patient in Patient.objects.filter(is_active=True, email_updates=True):
            week, pain = weekly_summary(patient), pain_trend(patient)
            if not week['reps'] and pain['this_week'] is None:
                lines = ["You didn't log any workouts or pain scores this week.",
                         "Even a short session helps. Your exercises are waiting on your dashboard."]
            else:
                change = f" ({week['change']:+d}% vs the week before)" if week['change'] is not None else ''
                lines = [f"  Reps:          {week['reps']}{change}", f"  Active days:   {week['active_days']} of 7"]
                if week['quality'] is not None:
                    lines.append(f"  Avg quality:   {week['quality']}%")
                lines.append(f"  Streak:        {exercise_streak(patient)} days")
                if pain['this_week'] is not None:
                    lines.append(f"  Average pain:  {pain['this_week']}/10" +
                                 (f" ({pain['change']:+.1f} vs the week before)" if pain['change'] is not None else ''))
            try:
                send_mail('Your week in ReViveCare',
                          f"Hi {patient.name},\n\nHere's your last 7 days:\n\n" + '\n'.join(lines) +
                          f"\n\nSee more: {settings.SITE_URL}/patient/history/\n\nKeep it up!\n", None, [patient.email])
                sent += 1
            except Exception as e:  # one bad address shouldn't stop the rest
                self.stderr.write(f"Weekly email for patient {patient.id} failed: {e}")
        self.stdout.write(f"Sent {sent} weekly progress email(s).")
