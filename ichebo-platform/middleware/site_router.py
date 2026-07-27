"""
SiteRouterMiddleware — sets request.site and request.urlconf based on the
incoming Host header. Serves sceptre.ichebo.org, learn.ichebo.org, and
bible.ichebo.org from the same Django process with per-request URL confs (ADR-023).
"""
from django.urls import set_urlconf


class SiteRouterMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()
        if host == 'sceptre.ichebo.org':
            request.site = 'community'
            request.urlconf = 'sceptre.urls'
            set_urlconf('sceptre.urls')
        elif host == 'learn.ichebo.org':
            request.site = 'learn'
            request.urlconf = 'learn.subdomain_urls'
            set_urlconf('learn.subdomain_urls')
        elif host == 'bible.ichebo.org':
            request.site = 'bible'
            request.urlconf = 'bible.subdomain_urls'
            set_urlconf('bible.subdomain_urls')
        else:
            request.site = 'agency'
            set_urlconf(None)

        response = self.get_response(request)
        set_urlconf(None)
        return response
