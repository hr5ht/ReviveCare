import json

from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.test import Client, TestCase

from .models import Patient


def post_json(client, url, data):
    return client.post(url, json.dumps(data), content_type='application/json')


class PatientLoginTests(TestCase):
    def setUp(self):
        cache.clear()
        self.patient = Patient.objects.create(name='Asha Rao', email='asha@example.com', info='ACL',
                                              password=make_password('Right-pass-1'))

    def login(self, password, email='asha@example.com', client=None):
        return post_json(client or self.client, '/api/patient/login/', {'email': email, 'password': password})

    def test_correct_password_logs_in(self):
        r = self.login('Right-pass-1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['patient']['email'], 'asha@example.com')
        self.assertEqual(self.client.session['patient_id'], self.patient.id)

    def test_reports_must_change_password(self):
        self.patient.must_change_password = True
        self.patient.save()
        self.assertTrue(self.login('Right-pass-1').json()['must_change_password'])

    def test_wrong_password_rejected(self):
        self.assertEqual(self.login('nope').status_code, 401)
        self.assertNotIn('patient_id', self.client.session)

    def test_unknown_email(self):
        self.assertEqual(self.login('x', email='nobody@example.com').status_code, 404)

    def test_missing_fields(self):
        self.assertEqual(post_json(self.client, '/api/patient/login/', {}).status_code, 400)

    def test_csrf_enforced(self):
        strict = Client(enforce_csrf_checks=True)
        self.assertEqual(self.login('Right-pass-1', client=strict).status_code, 403)

    def test_rate_limit_per_ip(self):
        other = Patient.objects.create(name='B', email='b@example.com', info='x', password=make_password('B-pass-123'))
        for i in range(10):
            self.login('wrong', email=other.email if i % 2 else 'asha@example.com')
        self.assertEqual(self.login('Right-pass-1').status_code, 429)

    def test_account_locks_after_five_failures(self):
        for _ in range(5):
            self.login('wrong')
        r = self.login('Right-pass-1')
        self.assertEqual(r.status_code, 423)
        self.patient.refresh_from_db()
        self.assertIsNotNone(self.patient.locked_until)

    def test_success_resets_failure_count(self):
        for _ in range(4):
            self.login('wrong')
        self.login('Right-pass-1')
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.failed_login_count, 0)
