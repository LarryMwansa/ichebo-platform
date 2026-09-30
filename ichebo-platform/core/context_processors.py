from django.conf import settings

_SUBDOMAIN_SHELLS = {
    'learn': 'learn/subdomain_shell.html',
    'bible': 'bible/subdomain_shell.html',
    'handbook': 'apostolic_chrome.html',
}


def htmx_base(request):
    """
    Returns 'base_partial.html' if it's an HTMX request, otherwise 'base.html'.
    Also injects shell_template: the correct workspace shell for the current
    site (learn.ichebo.org / bible.ichebo.org get lean participant shells;
    handbook.ichebo.org gets the Apostolic Chrome — currently only the Bible
    reader uses this dynamic lookup there, since Handbook's own pages extend
    workspace/handbook/base.html directly; everything else gets the full
    agency workspace_shell.html).
    """
    site = getattr(request, 'site', 'agency')
    shell = _SUBDOMAIN_SHELLS.get(site, 'workspace_shell.html')

    base = 'base_partial.html' if request.headers.get('HX-Request') else 'base.html'
    return {
        'base_template': base,
        'shell_template': shell,
        # Settings aren't reachable from templates; the nav needs this to send
        # Level 0 members to induction rather than the agency Formation app.
        'SCEPTRE_INDUCTION_URL': settings.SCEPTRE_INDUCTION_URL,
    }
