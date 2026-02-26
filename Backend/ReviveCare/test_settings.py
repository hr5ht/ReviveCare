"""Settings for `python manage.py test --settings=ReviveCare.test_settings`: no Postgres, SMTP or Groq needed."""
import os

os.environ.setdefault('SECRET_KEY', 'test-only-secret-key')
os.environ.pop('GROQ_API_KEY', None)

from .settings import *  # noqa: E402,F401,F403

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']  # fast; tests only
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = False
