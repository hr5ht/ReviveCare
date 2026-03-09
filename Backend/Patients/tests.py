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

    def test_duration_saved_and_never_shrinks(self):
        from .models import Workout
        self.save(reps=1, quality='good', duration_seconds=40)
        self.save(reps=2, quality='good', duration_seconds=35)  # an older request arriving late
        self.assertEqual(Workout.objects.get().duration_seconds, 40)

    def test_exercise_required(self):
        self.assertEqual(post_json(self.client, self.url, {'reps': 1}).status_code, 400)


class ChatbotParsingTests(TestCase):
    def parse(self, text):
        from types import SimpleNamespace
        from .views import parse_response
        return parse_response(SimpleNamespace(content=text))

    def test_plain_json(self):
        self.assertEqual(self.parse('{"patient_response": "Rest well.", "seriousness_score": 0.2}'), ('Rest well.', 0.2))

    def test_json_wrapped_in_text_or_code_fence(self):
        text = 'Sure!\n```json\n{"patient_response": "Call your doctor.", "seriousness_score": 0.8}\n```'
        self.assertEqual(self.parse(text), ('Call your doctor.', 0.8))

    def test_score_clamped_to_0_1(self):
        self.assertEqual(self.parse('{"patient_response": "x", "seriousness_score": 7}')[1], 1.0)
        self.assertEqual(self.parse('{"patient_response": "x", "seriousness_score": -2}')[1], 0.0)

    def test_unparseable_replies_fall_back_safely(self):
        for text in ['no json here', '{not valid json}', '{"patient_response": "x", "seriousness_score": "high"}']:
            reply, score = self.parse(text)
            self.assertIn('trouble processing', reply)
            self.assertEqual(score, 0.0)


class ChatbotEndpointTests(TestCase):
    url = '/patient/chatbot/send/'

    def setUp(self):
        cache.clear()
        Patient.objects.create(name='C', email='c@example.com', info='Knee', password=make_password('Right-pass-1'))
        post_json(self.client, '/api/patient/login/', {'email': 'c@example.com', 'password': 'Right-pass-1'})

    def send_with_reply(self, content):
        from types import SimpleNamespace
        from unittest import mock
        model = mock.Mock(invoke=mock.Mock(return_value=SimpleNamespace(content=content)))
        with mock.patch('Patients.views.LANGCHAIN_AVAILABLE', True), \
                mock.patch('Patients.views.initialize_model', return_value=model):
            return post_json(self.client, self.url, {'message': 'I have a fever', 'language': 'english'})

    def test_reply_and_history(self):
        r = self.send_with_reply('{"patient_response": "Drink water.", "seriousness_score": 0.3}').json()
        self.assertEqual((r['response'], r['seriousness_score']), ('Drink water.', 0.3))
        self.assertEqual(len(self.client.session['chat_history']), 2)

    def test_serious_reply_emails_the_doctor(self):
        from django.core import mail
        self.send_with_reply('{"patient_response": "Go to hospital.", "seriousness_score": 0.9}')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('I have a fever', mail.outbox[0].body)

    def test_model_failure_returns_friendly_503(self):
        from unittest import mock
        with mock.patch('Patients.views.LANGCHAIN_AVAILABLE', True), \
                mock.patch('Patients.views.initialize_model', side_effect=RuntimeError('no key')):
            r = post_json(self.client, self.url, {'message': 'hi'})
        self.assertEqual(r.status_code, 503)
        self.assertIn('contact your doctor', r.json()['error'])

    def test_requires_login(self):
        self.client.logout()
        self.assertFalse(post_json(self.client, self.url, {'message': 'hi'}).json()['success'])


class PatientDoctorLinkTests(TestCase):
    def test_new_patient_belongs_to_the_doctor_who_added_them(self):
        from django.contrib.auth.models import User
        doc = User.objects.create_user('doc', password='Doc-pass-123')
        self.client.login(username='doc', password='Doc-pass-123')
        post_json(self.client, '/api/patients/add/', {'name': 'Ravi', 'email': 'ravi@example.com', 'info': 'x'})
        self.assertEqual(Patient.objects.get().doctor, doc)
        self.assertEqual(list(doc.patients.all()), [Patient.objects.get()])

    def test_deleting_doctor_keeps_patient(self):
        from django.contrib.auth.models import User
        doc = User.objects.create_user('doc')
        p = Patient.objects.create(name='A', email='a@example.com', info='x', password='x', doctor=doc)
        doc.delete()
        p.refresh_from_db()
        self.assertIsNone(p.doctor)


class DoctorScopeTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.a = User.objects.create_user('a', password='Doc-pass-123')
        self.b = User.objects.create_user('b', password='Doc-pass-123')
        Patient.objects.create(name='Mine', email='mine@example.com', info='x', password='x', doctor=self.a)
        Patient.objects.create(name='Theirs', email='theirs@example.com', info='x', password='x', doctor=self.b)

    def test_doctor_lists_only_own_patients(self):
        self.client.login(username='a', password='Doc-pass-123')
        names = [p['name'] for p in self.client.get('/api/patients/').json()['patients']]
        self.assertEqual(names, ['Mine'])

    def test_superuser_sees_everyone(self):
        from django.contrib.auth.models import User
        User.objects.create_superuser('admin', 'a@example.com', 'Admin-pass-123')
        self.client.login(username='admin', password='Admin-pass-123')
        self.assertEqual(len(self.client.get('/api/patients/').json()['patients']), 2)


class AddPatientRecoveryDetailsTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        User.objects.create_user('doc', password='Doc-pass-123')
        self.client.login(username='doc', password='Doc-pass-123')

    def add(self, **extra):
        return post_json(self.client, '/api/patients/add/', {'name': 'Ravi', 'email': 'ravi@example.com', 'info': 'x', **extra})

    def test_saves_recovery_details(self):
        self.add(condition='Hip replacement', surgery_date='2026-01-15', phone='+91 98765 43210',
                 emergency_contact_name='Anil', emergency_contact_phone='+91 91234 56789')
        p = Patient.objects.get()
        self.assertEqual((p.condition, str(p.surgery_date), p.emergency_contact_name), ('Hip replacement', '2026-01-15', 'Anil'))

    def test_rejects_bad_or_future_surgery_date(self):
        self.assertEqual(self.add(surgery_date='not-a-date').status_code, 400)
        self.assertEqual(self.add(surgery_date='2999-01-01').status_code, 400)
        self.assertFalse(Patient.objects.exists())
