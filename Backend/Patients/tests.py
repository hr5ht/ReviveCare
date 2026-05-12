import json

from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.test import Client, TestCase

from .models import ChatMessage, Patient


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
        stored = list(Patient.objects.get(email='c@example.com').chat_messages.values_list('role', 'content', 'seriousness'))
        self.assertEqual(stored, [('user', 'I have a fever', None), ('assistant', 'Drink water.', 0.3)])

    def test_history_is_sent_to_the_model(self):
        self.send_with_reply('{"patient_response": "Drink water.", "seriousness_score": 0.3}')
        from types import SimpleNamespace
        from unittest import mock
        model = mock.Mock(invoke=mock.Mock(return_value=SimpleNamespace(content='{"patient_response": "ok", "seriousness_score": 0}')))
        with mock.patch('Patients.views.LANGCHAIN_AVAILABLE', True), mock.patch('Patients.views.initialize_model', return_value=model):
            post_json(self.client, self.url, {'message': 'Still hot'})
        sent = [m.content for m in model.invoke.call_args.args[0][1:]]
        self.assertEqual(sent, ['I have a fever', 'Drink water.', 'Still hot'])

    def test_serious_reply_emails_the_doctor(self):
        from unittest import mock
        from django.core import mail
        # Run the background email thread inline so the outbox is filled before we look
        inline = lambda target, args, **kw: mock.Mock(start=lambda: target(*args))
        with mock.patch('Patients.views.threading.Thread', inline):
            self.send_with_reply('{"patient_response": "Go to hospital.", "seriousness_score": 0.9}')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('I have a fever', mail.outbox[0].body)

    def test_streamed_reply(self):
        from types import SimpleNamespace
        from unittest import mock
        raw = '{"patient_response": "Drink water.", "seriousness_score": 0.3}'
        model = mock.Mock(stream=mock.Mock(return_value=[SimpleNamespace(content=raw[i:i + 7]) for i in range(0, len(raw), 7)]))
        with mock.patch('Patients.views.LANGCHAIN_AVAILABLE', True), mock.patch('Patients.views.initialize_model', return_value=model):
            r = post_json(self.client, self.url, {'message': 'I have a fever', 'stream': True})
        lines = [json.loads(l) for l in b''.join(r.streaming_content).decode().splitlines()]
        self.assertEqual(''.join(l.get('delta', '') for l in lines), 'Drink water.')
        self.assertEqual(lines[-1], {'done': True, 'id': ChatMessage.objects.get(role='assistant').id, 'response': 'Drink water.', 'seriousness_score': 0.3})
        self.assertEqual(Patient.objects.get(email='c@example.com').chat_messages.count(), 2)

    def test_new_conversation_hides_earlier_messages_from_model_and_page(self):
        self.send_with_reply('{"patient_response": "Drink water.", "seriousness_score": 0.3}')
        self.assertEqual(post_json(self.client, '/patient/chatbot/new/', {}).status_code, 200)
        self.assertNotIn('Drink water.', self.client.get('/patient/chat/').content.decode())
        from types import SimpleNamespace
        from unittest import mock
        model = mock.Mock(invoke=mock.Mock(return_value=SimpleNamespace(content='{"patient_response": "ok", "seriousness_score": 0}')))
        with mock.patch('Patients.views.LANGCHAIN_AVAILABLE', True), mock.patch('Patients.views.initialize_model', return_value=model):
            post_json(self.client, self.url, {'message': 'Fresh start'})
        self.assertEqual([m.content for m in model.invoke.call_args.args[0][1:]], ['Fresh start'])
        self.assertEqual(Patient.objects.get(email='c@example.com').chat_messages.count(), 4)  # the doctor still sees everything

    def test_feedback_on_own_replies_only(self):
        reply_id = self.send_with_reply('{"patient_response": "Drink water.", "seriousness_score": 0.3}').json()['id']
        other = Patient.objects.create(name='O', email='o@example.com', info='x', password='x')
        theirs = other.chat_messages.create(role='assistant', content='x')
        self.assertEqual(post_json(self.client, '/patient/chatbot/feedback/', {'id': reply_id, 'helpful': False}).status_code, 200)
        self.assertEqual(post_json(self.client, '/patient/chatbot/feedback/', {'id': theirs.id, 'helpful': True}).status_code, 404)
        self.assertIs(ChatMessage.objects.get(id=reply_id).helpful, False)
        self.assertIsNone(ChatMessage.objects.get(id=theirs.id).helpful)

    def test_reply_language_follows_the_picker(self):
        from types import SimpleNamespace
        from unittest import mock
        model = mock.Mock(invoke=mock.Mock(return_value=SimpleNamespace(content='{"patient_response": "ok", "seriousness_score": 0}')))
        with mock.patch('Patients.views.LANGCHAIN_AVAILABLE', True), mock.patch('Patients.views.initialize_model', return_value=model):
            post_json(self.client, self.url, {'message': 'hi', 'language': 'tamil'})
        self.assertIn('Write patient_response in Tamil', model.invoke.call_args.args[0][0].content)

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


class GoalProgressTests(TestCase):
    def setUp(self):
        from .models import Exercise
        self.patient = Patient.objects.create(name='G', email='g@example.com', info='x', password=make_password('Right-pass-1'))
        post_json(self.client, '/api/patient/login/', {'email': 'g@example.com', 'password': 'Right-pass-1'})
        self.curl = Exercise.objects.get(slug='bicep-curl')

    def goal(self, kind, target, exercise=None):
        from .models import RecoveryGoal
        return RecoveryGoal.objects.create(patient=self.patient, kind=kind, target=target, exercise=exercise)

    def save(self, reps, angle, exercise='bicep-curl', completed=False):
        return post_json(self.client, '/api/exercises/update-session/', {
            'exercise_id': exercise, 'target_reps': 10, 'reps': reps, 'angle': angle, 'quality': 'good', 'completed': completed})

    def test_reps_goal_reached_while_exercising(self):
        from .goals import progress
        goal = self.goal('total_reps', 3)
        self.save(1, 50)
        self.assertEqual(progress(goal)[:2], (1, 33))
        self.save(2, 50)
        r = self.save(3, 50)
        self.assertEqual(r.json()['goals_reached'], ['3 reps'])
        goal.refresh_from_db()
        self.assertIsNotNone(goal.achieved_at)

    def test_range_goal_respects_direction(self):
        from .goals import progress
        curl_goal = self.goal('range', 60, self.curl)  # curls: a smaller elbow angle is better
        self.save(1, 75)
        self.assertFalse(progress(curl_goal)[2])
        self.save(2, 58)
        self.assertEqual(progress(curl_goal), (58, 100, True))

    def test_exercise_filter_and_sessions(self):
        from .goals import progress
        goal = self.goal('sessions', 2, self.curl)
        self.save(1, 50, exercise='squat')
        self.assertEqual(progress(goal)[0], 0)
        self.save(1, 50)
        self.assertEqual(progress(goal)[0], 1)


class PartialReplyTests(TestCase):
    def test_decodes_growing_prefixes(self):
        from Patients.views import partial_reply
        full = '```json\n{"patient_response": "Rest \\"well\\"\\nIce it \\u00e9 \\\\ ok", "seriousness_score": 0.2}'
        seen = [partial_reply(full[:i]) for i in range(len(full) + 1)]
        self.assertEqual(seen[-1], 'Rest "well"\nIce it é \\ ok')
        for a, b in zip(seen, seen[1:]):
            self.assertTrue(b.startswith(a), (a, b))


class PainAlertTests(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(name='P', email='p@example.com', info='x', password='x')
        session = self.client.session
        session['patient_id'] = self.patient.id
        session.save()

    def log(self, pain, days_ago=0):
        """Today's entries go through the diary page (which runs the check); earlier ones are backdated directly."""
        if not days_ago:
            return self.client.post('/patient/diary/', {'pain': pain})
        from datetime import timedelta
        from django.utils import timezone
        from .models import DiaryEntry
        entry = DiaryEntry.objects.create(patient=self.patient, pain=pain)
        DiaryEntry.objects.filter(id=entry.id).update(created_at=timezone.now() - timedelta(days=days_ago))

    def test_steady_pain_does_not_alert(self):
        for d in (6, 5, 4, 2, 1, 0):
            self.log(4, d)
        self.assertFalse(self.patient.alerts.exists())

    def test_rising_pain_alerts_once_a_day(self):
        for d, pain in ((6, 3), (5, 3), (4, 3), (2, 5), (1, 6)):
            self.log(pain, d)
        self.log(2)  # last 3 days average 4.3 vs 3.0 before: not enough
        self.assertFalse(self.patient.alerts.exists())
        self.log(7)  # today now averages 4.5, so the last 3 days average 5.2: alert
        self.log(7)  # still rising, but one alert a day
        self.assertEqual(self.patient.alerts.count(), 1)
        self.assertIn('Pain rising', self.patient.alerts.get().message)

    def test_severe_pain_alerts(self):
        self.log(9)
        self.assertIn('Pain severe', self.patient.alerts.get().message)


class VitalsAlertTests(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(name='V', email='v@example.com', info='x', password='x')
        session = self.client.session
        session['patient_id'] = self.patient.id
        session.save()

    def post(self, **readings):
        return self.client.post('/patient/vitals/', {'systolic': '', 'diastolic': '', 'heart_rate': '', 'temperature': '', **readings})

    def test_normal_readings_do_not_alert(self):
        self.post(systolic=128, diastolic=82, heart_rate=76, temperature='98.6')
        self.assertFalse(self.patient.alerts.exists())

    def test_fever_and_fast_heart_rate_alert_once_a_day(self):
        self.post(heart_rate=130, temperature='101.2')
        self.post(temperature='101.5')
        alert = self.patient.alerts.get()
        self.assertIn('Temperature 101.2 °F (above 100.4 °F)', alert.message)
        self.assertIn('Heart rate 130 bpm', alert.message)


class MedicationReminderTests(TestCase):
    def test_reminds_only_untaken_doses_in_the_window(self):
        from datetime import timedelta
        from django.core import mail
        from django.core.management import call_command
        from django.utils import timezone
        from .models import DoseTaken, Medication
        soon = (timezone.localtime() + timedelta(minutes=10)).strftime('%H:%M')
        later = (timezone.localtime() + timedelta(hours=3)).strftime('%H:%M')
        p = Patient.objects.create(name='M', email='m@example.com', info='x', password='x')
        due = Medication.objects.create(patient=p, name='Paracetamol', times=[soon, later])
        done = Medication.objects.create(patient=p, name='Aspirin', times=[soon])
        DoseTaken.objects.create(medication=done, date=timezone.localdate(), time=soon)
        call_command('send_medication_reminders', stdout=open('/dev/null', 'w'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(f'{soon}  Paracetamol', mail.outbox[0].body)
        self.assertNotIn('Aspirin', mail.outbox[0].body)
        self.assertNotIn(later, mail.outbox[0].body)


class MessageEmailTests(TestCase):
    def test_first_unread_message_emails_the_other_side(self):
        from unittest import mock
        from django.contrib.auth.models import User
        from django.core import mail
        doctor = User.objects.create_user('doc', email='doc@example.com', password='Doc-pass-123', first_name='Meera')
        p = Patient.objects.create(name='Asha', email='asha@example.com', info='x', password='x', doctor=doctor)
        session = self.client.session
        session['patient_id'] = p.id
        session.save()
        inline = lambda target, **kw: mock.Mock(start=target)
        with mock.patch('Home.views.threading.Thread', inline):
            self.client.post('/patient/messages/', {'body': 'Stairs hurt'})
            self.client.post('/patient/messages/', {'body': 'Also my knee clicks'})  # still unread: no second email
            self.assertEqual([m.to for m in mail.outbox], [['doc@example.com']])
            self.assertIn('Stairs hurt', mail.outbox[0].body)
            self.client.force_login(doctor)
            self.client.post(f'/doctor/inbox/{p.id}/', {'body': 'Keep icing'})
        self.assertEqual(mail.outbox[-1].to, ['asha@example.com'])
        self.assertIn('Dr. Meera sent you a message', mail.outbox[-1].body)


class NextAppointmentTests(TestCase):
    def test_dashboard_shows_next_upcoming_appointment(self):
        from datetime import timedelta
        from django.utils import timezone
        from .models import Appointment
        p = Patient.objects.create(name='N', email='n@example.com', info='x', password='x')
        session = self.client.session
        session['patient_id'] = p.id
        session.save()
        now = timezone.now()
        self.assertContains(self.client.get('/patient/dashboard/'), 'Nothing booked yet')
        Appointment.objects.create(patient=p, starts_at=now - timedelta(days=1), reason='Past visit')
        Appointment.objects.create(patient=p, starts_at=now + timedelta(days=1), reason='Cancelled visit', status='cancelled')
        Appointment.objects.create(patient=p, starts_at=now + timedelta(days=3), reason='Later visit')
        Appointment.objects.create(patient=p, starts_at=now + timedelta(days=2), reason='Knee follow-up', location='Room 4')
        r = self.client.get('/patient/dashboard/')
        self.assertContains(r, 'Knee follow-up')
        self.assertContains(r, 'Room 4')
        for other in ('Past visit', 'Cancelled visit', 'Later visit', 'Nothing booked yet'):
            self.assertNotContains(r, other)


class RescheduleRequestTests(TestCase):
    def test_patient_asks_to_move_next_appointment(self):
        from datetime import timedelta
        from unittest import mock
        from django.contrib.auth.models import User
        from django.core import mail
        from django.utils import timezone
        from .models import Appointment
        doctor = User.objects.create_user('doc', email='doc@example.com', password='Doc-pass-123')
        p = Patient.objects.create(name='R', email='r@example.com', info='x', password='x', doctor=doctor)
        other = Patient.objects.create(name='O', email='o@example.com', info='x', password='x')
        session = self.client.session
        session['patient_id'] = p.id
        session.save()
        appt = Appointment.objects.create(patient=p, doctor=doctor, starts_at=timezone.now() + timedelta(days=2))
        theirs = Appointment.objects.create(patient=other, starts_at=timezone.now() + timedelta(days=2))
        self.assertContains(self.client.get('/patient/dashboard/'), 'Ask to reschedule')
        inline = lambda target, **kw: mock.Mock(start=target)
        with mock.patch('Home.views.threading.Thread', inline):
            self.client.post(f'/patient/appointments/{appt.id}/reschedule/', {'note': 'Weekday after 4 pm'})
            self.client.post(f'/patient/appointments/{theirs.id}/reschedule/', {'note': 'not mine'})
        appt.refresh_from_db(); theirs.refresh_from_db()
        self.assertEqual(appt.reschedule_request, 'Weekday after 4 pm')
        self.assertEqual(theirs.reschedule_request, '')
        self.assertIn('Weekday after 4 pm', p.messages.get().body)
        self.assertEqual(mail.outbox[0].to, ['doc@example.com'])
        r = self.client.get('/patient/dashboard/')
        self.assertContains(r, 'You asked to reschedule')
        self.assertNotContains(r, 'Ask to reschedule')


class MeetingLinkTests(TestCase):
    def test_doctor_adds_video_link_patient_sees_join_button(self):
        from datetime import timedelta
        from django.contrib.auth.models import User
        from django.utils import timezone
        doctor = User.objects.create_user('doc', password='Doc-pass-123')
        p = Patient.objects.create(name='T', email='t@example.com', info='x', password='x', doctor=doctor)
        self.client.force_login(doctor)
        when = timezone.localtime(timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        url = f'/doctor/patients/{p.id}/appointments/'
        self.client.post(url, {'starts_at': when, 'duration_minutes': 30, 'meeting_url': 'javascript:alert(1)'})
        self.assertFalse(p.appointments.exists())
        self.client.post(url, {'starts_at': when, 'duration_minutes': 30, 'meeting_url': 'https://meet.example.com/abc'})
        self.assertEqual(p.appointments.get().meeting_url, 'https://meet.example.com/abc')
        session = self.client.session
        session['patient_id'] = p.id
        session.save()
        r = self.client.get('/patient/dashboard/')
        self.assertContains(r, 'Join video call')
        self.assertContains(r, 'href="https://meet.example.com/abc"')


class AppointmentCalendarFileTests(TestCase):
    def test_ics_download_is_scoped_to_the_patient(self):
        from datetime import datetime, timezone as tz
        from .models import Appointment
        p = Patient.objects.create(name='C', email='c@example.com', info='x', password='x')
        other = Patient.objects.create(name='D', email='d@example.com', info='x', password='x')
        a = Appointment.objects.create(patient=p, starts_at=datetime(2026, 6, 1, 4, 30, tzinfo=tz.utc), duration_minutes=45,
                                       reason='Knee check, week 6', meeting_url='https://meet.example.com/x')
        theirs = Appointment.objects.create(patient=other, starts_at=a.starts_at)
        session = self.client.session
        session['patient_id'] = p.id
        session.save()
        r = self.client.get(f'/patient/appointments/{a.id}/calendar.ics')
        self.assertEqual(r['Content-Type'], 'text/calendar; charset=utf-8')
        body = r.content.decode()
        for line in ('DTSTART:20260601T043000Z', 'DTEND:20260601T051500Z', 'SUMMARY:Knee check\\, week 6', 'URL:https://meet.example.com/x'):
            self.assertIn(line + '\r\n', body)
        self.assertEqual(self.client.get(f'/patient/appointments/{theirs.id}/calendar.ics').status_code, 404)


class AppointmentReminderTests(TestCase):
    def test_reminds_appointments_a_day_out_once(self):
        from datetime import timedelta
        from django.core import mail
        from django.core.management import call_command
        from django.utils import timezone
        from .models import Appointment
        p = Patient.objects.create(name='Asha', email='a@example.com', info='x', password='x')
        now = timezone.now()
        Appointment.objects.create(patient=p, starts_at=now + timedelta(hours=24, minutes=30), reason='Knee review', location='Room 2')
        Appointment.objects.create(patient=p, starts_at=now + timedelta(hours=26), reason='Too far')
        Appointment.objects.create(patient=p, starts_at=now + timedelta(hours=24, minutes=10), reason='Cancelled one', status='cancelled')
        call_command('send_appointment_reminders', stdout=open('/dev/null', 'w'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Knee review', mail.outbox[0].body)
        self.assertIn('Where: Room 2', mail.outbox[0].body)


class NotificationBellTests(TestCase):
    def test_bell_counts_only_own_unread(self):
        from django.utils import timezone
        from .models import Notification
        p = Patient.objects.create(name='B', email='b@example.com', info='x', password='x')
        other = Patient.objects.create(name='O', email='o@example.com', info='x', password='x')
        Notification.objects.create(patient=p, title='New plan')
        Notification.objects.create(patient=p, title='Seen', read_at=timezone.now())
        Notification.objects.create(patient=other, title='Not yours')
        session = self.client.session
        session['patient_id'] = p.id
        session.save()
        self.assertContains(self.client.get('/patient/dashboard/'), 'aria-label="Notifications, 1 unread"')
        r = self.client.get('/patient/notifications/')
        self.assertContains(r, 'New plan')
        self.assertNotContains(r, 'Not yours')


class NotificationReadTests(TestCase):
    def test_opening_and_mark_all(self):
        from .models import Notification
        p = Patient.objects.create(name='R', email='r@example.com', info='x', password='x')
        other = Patient.objects.create(name='O', email='o@example.com', info='x', password='x')
        a = Notification.objects.create(patient=p, title='Plan', link='/patient/exercises/')
        evil = Notification.objects.create(patient=p, title='Odd', link='//evil.example.com/')
        theirs = Notification.objects.create(patient=other, title='Not yours')
        session = self.client.session
        session['patient_id'] = p.id
        session.save()
        self.assertRedirects(self.client.get(f'/patient/notifications/{a.id}/'), '/patient/exercises/', fetch_redirect_response=False)
        a.refresh_from_db()
        self.assertIsNotNone(a.read_at)
        self.assertRedirects(self.client.get(f'/patient/notifications/{evil.id}/'), '/patient/notifications/', fetch_redirect_response=False)
        Notification.objects.create(patient=p, title='Another')
        self.client.post('/patient/notifications/read/')
        self.assertFalse(p.notifications.filter(read_at=None).exists())
        self.assertFalse(Notification.objects.get(id=theirs.id).read_at)


class EmailPreferenceTests(TestCase):
    def test_turning_off_reminders_and_updates(self):
        from datetime import timedelta
        from unittest import mock
        from django.contrib.auth.models import User
        from django.core import mail
        from django.core.management import call_command
        from django.utils import timezone
        from .models import Appointment
        doctor = User.objects.create_user('doc', password='Doc-pass-123')
        p = Patient.objects.create(name='E', email='e@example.com', info='x', password='x', doctor=doctor)
        session = self.client.session
        session['patient_id'] = p.id
        session.save()
        self.client.post('/patient/profile/', {'email_prefs': '1', 'email_updates': 'on'})
        p.refresh_from_db()
        self.assertEqual((p.email_reminders, p.email_updates), (False, True))
        Appointment.objects.create(patient=p, starts_at=timezone.now() + timedelta(hours=24, minutes=5))
        call_command('send_appointment_reminders', stdout=open('/dev/null', 'w'))
        self.assertEqual(mail.outbox, [])
        p.email_updates = False
        p.save()
        self.client.force_login(doctor)
        with mock.patch('Home.views.threading.Thread', lambda target, **kw: mock.Mock(start=target)):
            self.client.post(f'/doctor/inbox/{p.id}/', {'body': 'Hello'})
        self.assertEqual(mail.outbox, [])


class PatientNotifyTests(TestCase):
    def test_plan_and_appointment_changes_notify_the_patient(self):
        from datetime import timedelta
        from unittest import mock
        from django.contrib.auth.models import User
        from django.core import mail
        from django.utils import timezone
        from .models import Exercise
        doctor = User.objects.create_user('doc', password='Doc-pass-123', first_name='Meera')
        p = Patient.objects.create(name='N', email='n@example.com', info='x', password='x', doctor=doctor)
        ex = Exercise.objects.filter(is_active=True).first()
        self.client.force_login(doctor)
        when = timezone.localtime(timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        with mock.patch('Home.views.threading.Thread', lambda target, **kw: mock.Mock(start=target)):
            self.client.post(f'/doctor/patients/{p.id}/plan/', {'exercise': [ex.id], f'reps_{ex.id}': 10, f'sets_{ex.id}': 3})
            self.client.post(f'/doctor/patients/{p.id}/appointments/', {'starts_at': when, 'duration_minutes': 30, 'reason': 'Review'})
            self.client.post(f'/doctor/patients/{p.id}/appointments/', {'cancel': p.appointments.get().id})
        titles = list(p.notifications.order_by('id').values_list('title', flat=True))
        self.assertEqual(titles, ['Your exercise plan was updated', 'Appointment booked', 'Appointment cancelled'])
        self.assertIn(f'Dr. Meera set your plan: {ex.name}.', p.notifications.order_by('id').first().body)
        self.assertEqual(len(mail.outbox), 3)


class PatientReportTests(TestCase):
    def test_report_only_for_own_patients(self):
        from django.contrib.auth.models import User
        from .models import Workout
        doctor = User.objects.create_user('doc', password='Doc-pass-123')
        stranger = User.objects.create_user('other', password='Doc-pass-123')
        p = Patient.objects.create(name='Rep', email='rep@example.com', info='x', password='x', doctor=doctor)
        Workout.objects.create(patient=p, exercise='squat', total_reps=12, excellent_reps=12)
        self.client.force_login(doctor)
        r = self.client.get(f'/doctor/patients/{p.id}/report/')
        self.assertContains(r, 'Progress report')
        self.assertContains(r, '<td class="py-1.5 text-right">12</td>', html=False)
        self.client.force_login(stranger)
        self.assertEqual(self.client.get(f'/doctor/patients/{p.id}/report/').status_code, 404)


class WorkoutCsvTests(TestCase):
    def test_csv_export(self):
        import csv, io
        from django.contrib.auth.models import User
        from .models import Workout
        doctor = User.objects.create_user('doc', password='Doc-pass-123')
        p = Patient.objects.create(name='Asha Rao', email='csv@example.com', info='x', password='x', doctor=doctor)
        Workout.objects.create(patient=p, exercise='squat', total_reps=10, good_reps=10, completed=True)
        self.client.force_login(doctor)
        r = self.client.get(f'/doctor/patients/{p.id}/workouts.csv')
        self.assertEqual(r['Content-Disposition'], 'attachment; filename="asha-rao-workouts.csv"')
        rows = list(csv.reader(io.StringIO(r.content.decode())))
        self.assertEqual(rows[0][:3], ['date', 'exercise', 'reps'])
        self.assertEqual(rows[1][2:], ['10', '10', '0', '10', '0', '70.0', '0', 'yes'])
        self.client.force_login(User.objects.create_user('x', password='Doc-pass-123'))
        self.assertEqual(self.client.get(f'/doctor/patients/{p.id}/workouts.csv').status_code, 404)
