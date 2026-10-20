"""Neon Auth (managed Better Auth) over its REST API (stdlib only).

Accounts live in this same Neon database, in the neon_auth schema. Django keeps doctor users, patients and sessions:
a sign-in is checked against Neon Auth, then matched to the Django user or patient with the same email.

Neon Auth's sign-up endpoint is public, so anyone could open an account in someone else's name. Only accounts this app
created, or whose owner used a reset code sent to that inbox, are marked emailVerified, and only those sign in here.
"""
import json
import logging
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.utils.crypto import get_random_string

logger = logging.getLogger(__name__)


class AuthError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code = status, code


def _call(path, body, cookie=None):
    """POST to Neon Auth. Returns the JSON reply and the session cookie it set ('' if none)."""
    base = settings.NEON_AUTH_BASE_URL
    if not base:
        raise ImproperlyConfigured('Set NEON_AUTH_BASE_URL (Neon Console → Auth → Configuration).')
    # Better Auth always trusts its own origin. These are server-to-server calls, so there's no browser to guard.
    headers = {'Content-Type': 'application/json', 'User-Agent': 'ReViveCare/1.0',
               'Origin': '{0.scheme}://{0.netloc}'.format(urlsplit(base))}
    if cookie:
        headers['Cookie'] = cookie
    req = urllib.request.Request(f'{base}/{path}', method='POST', headers=headers, data=json.dumps(body).encode())
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            cookies = '; '.join(c.split(';', 1)[0] for c in r.headers.get_all('Set-Cookie') or [])
            return json.loads(r.read() or b'{}'), cookies
    except urllib.error.HTTPError as e:
        try:
            data = json.loads(e.read() or b'{}')
        except ValueError:
            data = {}
        raise AuthError(e.code, data.get('code', ''), data.get('message') or str(e)) from None


def _mark_verified(email):
    with connection.cursor() as c:
        c.execute('UPDATE neon_auth."user" SET "emailVerified" = true WHERE email = %s', [email])


def sign_in(email, password):
    """The Neon Auth session cookie for a correct email and password on a trusted account, else None."""
    try:
        data, cookie = _call('sign-in/email', {'email': email, 'password': password})
    except AuthError as e:
        if e.status in (400, 401, 403):  # wrong password, unknown or malformed email
            return None
        raise
    return cookie if data['user']['emailVerified'] else None


def change_password(email, current, new):
    """False if the current password is wrong. Raises AuthError if Neon Auth refuses the new one."""
    cookie = sign_in(email, current)
    if not cookie:
        return False
    _call('change-password', {'currentPassword': current, 'newPassword': new}, cookie)
    return True


def create_user(email, password, name):
    """Create a trusted account. False if the email already has one."""
    try:
        _call('sign-up/email', {'email': email, 'password': password, 'name': name})
    except AuthError as e:
        if e.status == 422:  # USER_ALREADY_EXISTS
            return False
        raise
    _mark_verified(email)
    return True


def temp_password():
    """A first password for an account someone else creates. No look-alike characters (0/O, 1/l/I), so it's easy to read out."""
    return get_random_string(10, 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789')


def send_reset_code(email, name):
    """Have Neon Auth email a one-time code for choosing a new password. Creates the account first if this email has
    none yet, which is how people added before Neon Auth get one."""
    create_user(email, get_random_string(32), name)
    _call('email-otp/request-password-reset', {'email': email})


def reset_with_code(email, code, password):
    """Set a new password with the emailed code. False if the code is wrong or expired (a code allows a few tries).
    Raises AuthError if Neon Auth refuses the password."""
    try:
        _call('email-otp/reset-password', {'email': email, 'otp': code, 'password': password})
    except AuthError as e:
        if e.code in ('INVALID_OTP', 'OTP_EXPIRED', 'TOO_MANY_ATTEMPTS'):
            return False
        raise
    _mark_verified(email)  # the code reached this inbox
    return True


class NeonAuthBackend(ModelBackend):
    """Doctor and admin sign-in: the login form's username is the email, checked against Neon Auth."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        email = (username or '').strip().lower()
        if not email or not password:
            return None
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        try:
            return user if user and sign_in(email, password) else None
        except AuthError:  # Neon Auth down or rate limiting: the form says the sign-in failed
            logger.exception('Neon Auth sign-in failed')
            return None
