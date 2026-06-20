from datetime import timedelta

from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand
from django.utils import timezone

from Doctor.models import AuditLog
from Patients.models import Notification


class Command(BaseCommand):
    help = 'Delete expired sessions, old read notifications and audit entries past retention. Run daily, e.g. cron "30 3 * * *".'

    def add_arguments(self, parser):
        parser.add_argument('--notification-days', type=int, default=90, help='Keep read notifications this long')
        parser.add_argument('--audit-days', type=int, default=730, help='Keep audit log entries this long (check your retention rules)')

    def handle(self, notification_days, audit_days, **options):
        now = timezone.now()
        sessions = Session.objects.filter(expire_date__lt=now).delete()[0]
        notifications = Notification.objects.filter(read_at__lt=now - timedelta(days=notification_days)).delete()[0]
        audit = AuditLog.objects.filter(created_at__lt=now - timedelta(days=audit_days)).delete()[0]
        self.stdout.write(f"Deleted {sessions} expired session(s), {notifications} old notification(s), {audit} old audit entr{'y' if audit == 1 else 'ies'}.")
