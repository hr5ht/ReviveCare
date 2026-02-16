PERMISSIONS_POLICY = 'camera=(self), microphone=(self), geolocation=(), payment=(), usb=()'

# Only this site and the two CDNs the pages load from (Tailwind/MediaPipe on jsDelivr, lucide on unpkg).
# 'unsafe-inline' stays until inline scripts/onclick handlers move to static files; 'wasm-unsafe-eval' is for MediaPipe.
CDNS = 'https://cdn.jsdelivr.net https://unpkg.com'
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
