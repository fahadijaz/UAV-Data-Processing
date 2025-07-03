import re
from django.conf import settings
from django.shortcuts import redirect

EXEMPT_URLS = [
    re.compile(settings.LOGIN_URL.lstrip('/')),
    re.compile(r'^accounts/logout/$'),
    re.compile(r'^admin/'),
    re.compile(r'^static/'),
]

class LoginRequiredMiddleware:
    """
    Redirect any anonymous user to LOGIN_URL if they try to hit
    any URL not in EXEMPT_URLS.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info.lstrip('/')
        if not request.user.is_authenticated:
            if not any(pattern.match(path) for pattern in EXEMPT_URLS):
                return redirect(settings.LOGIN_URL)
        return self.get_response(request)
