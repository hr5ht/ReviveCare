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


class AddPatientTests(TestCase):
    url = '/api/patients/add/'

    def setUp(self):
        from django.contrib.auth.models import User
        User.objects.create_user('doc', password='Doc-pass-123')
        self.client.login(username='doc', password='Doc-pass-123')

    def add(self, **data):
        return post_json(self.client, self.url, {'name': 'Ravi Kumar', 'email': 'ravi@example.com', 'info': 'Hip', **data})

    def test_requires_doctor_login(self):
        self.client.logout()
        self.assertEqual(self.add().status_code, 401)
        self.assertFalse(Patient.objects.exists())

    def test_creates_patient_with_hashed_temporary_password(self):
        r = self.add().json()
        patient = Patient.objects.get(email='ravi@example.com')
        self.assertTrue(patient.must_change_password)
        self.assertNotEqual(patient.password, r['temporary_password'])
        self.assertTrue(patient.check_password(r['temporary_password']) if hasattr(patient, 'check_password')
                        else __import__('django.contrib.auth.hashers', fromlist=['x']).check_password(r['temporary_password'], patient.password))

    def test_temporary_passwords_are_unique_and_readable(self):
        a = self.add().json()['temporary_password']
        b = self.add(email='other@example.com').json()['temporary_password']
        self.assertNotEqual(a, b)
        self.assertEqual(len(a), 10)
        self.assertFalse(set(a) & set('0O1lI'))

    def test_email_lowercased_and_duplicates_rejected(self):
        self.add(email='Ravi@Example.com')
        r = self.add()
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Patient.objects.count(), 1)

    def test_name_and_email_required(self):
        self.assertEqual(self.add(name='').status_code, 400)
        self.assertEqual(self.add(email='').status_code, 400)

    def test_sends_welcome_email(self):
        from django.core import mail
        r = self.add().json()
        self.assertTrue(r['email_sent'])
        self.assertEqual(mail.outbox[0].to, ['ravi@example.com'])
        self.assertIn(r['temporary_password'], mail.outbox[0].body)

    def test_email_failure_still_creates_patient(self):
        with self.settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend', EMAIL_HOST='127.0.0.1',
                           EMAIL_PORT=1, EMAIL_TIMEOUT=1):
            r = self.add().json()
        self.assertTrue(r['success'])
        self.assertFalse(r['email_sent'])
        self.assertTrue(Patient.objects.filter(email='ravi@example.com').exists())


class WorkoutSessionTests(TestCase):
    url = '/api/exercises/update-session/'

    def setUp(self):
        self.patient = Patient.objects.create(name='S', email='s@example.com', info='x',
                                              password=make_password('Right-pass-1'))
        post_json(self.client, '/api/patient/login/', {'email': 's@example.com', 'password': 'Right-pass-1'})

    def save(self, **data):
        return post_json(self.client, self.url, {'exercise_id': 'bicep-curl', 'target_reps': 12, **data})

    def test_requires_patient_login(self):
        self.client.logout()
        self.assertEqual(self.save(reps=1).status_code, 401)

    def test_one_row_per_exercise_per_day(self):
        from .models import Workout
        self.save(reps=1, quality='excellent')
        self.save(reps=2, quality='good')
        post_json(self.client, self.url, {'exercise_id': 'jumping-jacks', 'reps': 5})
        self.assertEqual(Workout.objects.count(), 2)
        w = Workout.objects.get(exercise='bicep-curl')
        self.assertEqual((w.total_reps, w.target_reps, len(w.angles_data)), (2, 12, 2))

    def test_quality_counted_once_per_rep(self):
        from .models import Workout
        self.save(reps=1, quality='excellent')
        self.save(reps=1, quality='transition')
        self.save(reps=2, quality='good')
        self.save(reps=2, quality='good')
        w = Workout.objects.get()
        self.assertEqual((w.excellent_reps, w.good_reps, w.partial_reps), (1, 1, 0))

    def test_completed_session_starts_a_new_row(self):
        from .models import Workout
        self.save(reps=12, quality='excellent', completed=True)
        self.save(reps=1, quality='good')
        self.assertEqual(Workout.objects.filter(completed=True).count(), 1)
        self.assertEqual(Workout.objects.filter(completed=False).count(), 1)

    def test_exercise_required(self):
        self.assertEqual(post_json(self.client, self.url, {'reps': 1}).status_code, 400)
