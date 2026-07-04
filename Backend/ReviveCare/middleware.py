import json
import logging
import time

PERMISSIONS_POLICY = 'camera=(self), microphone=(self), geolocation=(), payment=(), usb=()'

# Only this site and jsDelivr (MediaPipe Pose); CSS and icons are served locally.
# 'unsafe-inline' stays until inline scripts/onclick handlers move to static files; 'wasm-unsafe-eval' is for MediaPipe.
CDNS = 'https://cdn.jsdelivr.net'
CONTENT_SECURITY_POLICY = '; '.join([
    "default-src 'self'",
    f"script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval' {CDNS}",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "media-src 'self' blob:",
    f"connect-src 'self' {CDNS}",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
])


def security_headers(get_response):
    """Headers Django doesn't set by default (it already sends nosniff, Referrer-Policy and X-Frame-Options)."""
    def middleware(request):
        response = get_response(request)
        response.setdefault('Permissions-Policy', PERMISSIONS_POLICY)
        response.setdefault('Content-Security-Policy', CONTENT_SECURITY_POLICY)
        return response
    return middleware


request_logger = logging.getLogger('revivecare.requests')


def request_log(get_response):
    """One JSON line per request (method, path, status, duration, who) for Vercel's log search.
    Query strings are left out: patient searches put names in them."""
    def middleware(request):
        start = time.monotonic()
        response = get_response(request)
        if not request.path.startswith('/static/'):
            user = getattr(request, 'user', None)
            entry = {
                'method': request.method,
                'path': request.path,
                'status': response.status_code,
                'ms': round((time.monotonic() - start) * 1000),
                'request_id': request.headers.get('x-vercel-id', ''),
                'doctor': user.id if user is not None and user.is_authenticated else None,
                'patient': request.session.get('patient_id') if hasattr(request, 'session') else None,
            }
            # WARNING at most: Django already logs 5xx tracebacks at ERROR, and Sentry would report those twice
            level = logging.WARNING if response.status_code >= 400 else logging.INFO
            request_logger.log(level, json.dumps(entry))
        return response
    return middleware
