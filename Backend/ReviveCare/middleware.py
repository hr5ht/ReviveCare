PERMISSIONS_POLICY = 'camera=(self), microphone=(self), geolocation=(), payment=(), usb=()'


def security_headers(get_response):
    """Headers Django doesn't set by default (it already sends nosniff, Referrer-Policy and X-Frame-Options)."""
    def middleware(request):
        response = get_response(request)
        response.setdefault('Permissions-Policy', PERMISSIONS_POLICY)
        return response
    return middleware
