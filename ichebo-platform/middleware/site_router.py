"""
SiteRouterMiddleware — sets request.site and request.urlconf based on the
incoming Host header. Serves sceptre.ichebo.org from the same Django
process as app.ichebo.org, with its own URL conf (ADR-023).

request.urlconf is the real Django mechanism for per-request URL conf
override — the resolver checks it automatically on every request, no
separate dispatcher function in ics_project/urls.py is needed.
"""


class SiteRouterMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()
        if host == 'sceptre.ichebo.org':
            request.site = 'community'
            request.urlconf = 'sceptre.urls'
        elif host == 'learn.ichebo.org':
            request.site = 'learn'
            request.urlconf = 'learn.subdomain_urls'
        elif host == 'bible.ichebo.org':
            request.site = 'bible'
            request.urlconf = 'bible.subdomain_urls'
        else:
            request.site = 'agency'
            # request.urlconf left unset — Django falls back to ROOT_URLCONF
        return self.get_response(request)
