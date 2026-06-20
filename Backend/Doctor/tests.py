from django.contrib.auth.models import User
from django.test import TestCase

from Patients.models import Patient

PAGES = ['/doctor/', '/doctor/alerts/', '/doctor/calendar/', '/doctor/inbox/', '/doctor/profile/', '/doctor/add-patient/']
PATIENT_PAGES = ['', 'edit/', 'plan/', 'report/', 'workouts.csv', 'medications/', 'goals/']
PATIENT_POSTS = ['active/', 'notes/', 'appointments/', 'medications/', 'goals/', 'plan/']


class DoctorAuthTests(TestCase):
    def setUp(self):
        self.doc = User.objects.create_user('doc', password='Doc-pass-123')
        self.other = User.objects.create_user('other', password='Doc-pass-123')
        self.mine = Patient.objects.create(name='Mine', email='mine@example.com', info='x', password='x', doctor=self.doc)
        self.theirs = Patient.objects.create(name='Theirs', email='theirs@example.com', info='x', password='x', doctor=self.other)

    def test_pages_need_a_signed_in_doctor(self):
        for url in PAGES + [f'/doctor/patients/{self.mine.id}/{p}' for p in PATIENT_PAGES] + [f'/doctor/inbox/{self.mine.id}/']:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 302, url)
            self.assertTrue(r['Location'].startswith('/doctor/login/'), url)

    def test_signed_in_patient_is_not_a_doctor(self):
        session = self.client.session
        session['patient_id'] = self.mine.id
        session.save()
        r = self.client.get(f'/doctor/patients/{self.mine.id}/')
        self.assertTrue(r['Location'].startswith('/doctor/login/'))

    def test_own_patient_pages_load(self):
        self.client.force_login(self.doc)
        for url in PAGES + [f'/doctor/patients/{self.mine.id}/{p}' for p in PATIENT_PAGES] + [f'/doctor/inbox/{self.mine.id}/']:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_other_doctors_patients_are_hidden(self):
        self.client.force_login(self.doc)
        for p in PATIENT_PAGES:
            self.assertEqual(self.client.get(f'/doctor/patients/{self.theirs.id}/{p}').status_code, 404, p)
        for p in PATIENT_POSTS:
            self.assertEqual(self.client.post(f'/doctor/patients/{self.theirs.id}/{p}', {'text': 'x', 'active': '0'}).status_code, 404, p)
        self.assertEqual(self.client.get(f'/doctor/inbox/{self.theirs.id}/').status_code, 404)
        self.theirs.refresh_from_db()
        self.assertTrue(self.theirs.is_active)
        self.assertFalse(self.theirs.notes.exists())

    def test_superuser_can_open_any_patient(self):
        self.client.force_login(User.objects.create_superuser('root', 'root@example.com', 'Root-pass-123'))
        self.assertEqual(self.client.get(f'/doctor/patients/{self.theirs.id}/').status_code, 200)

    def test_login_logout(self):
        r = self.client.post('/doctor/login/', {'username': 'doc', 'password': 'wrong'})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
        r = self.client.post('/doctor/login/', {'username': 'doc', 'password': 'Doc-pass-123'})
        self.assertRedirects(r, '/doctor/', fetch_redirect_response=False)
        self.assertEqual(self.client.get('/doctor/logout/').status_code, 405)  # logging out takes a POST
        self.client.post('/doctor/logout/')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_deactivated_doctor_cannot_sign_in(self):
        self.doc.is_active = False
        self.doc.save()
        self.client.post('/doctor/login/', {'username': 'doc', 'password': 'Doc-pass-123'})
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_api_needs_a_doctor(self):
        self.assertIn(self.client.get('/api/patients/').status_code, (401, 403))
        self.client.force_login(self.doc)
        self.assertEqual(self.client.get('/api/patients/').status_code, 200)
