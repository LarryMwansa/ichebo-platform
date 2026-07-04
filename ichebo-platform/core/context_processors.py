_SUBDOMAIN_SHELLS = {
    'learn': 'workspace_shell.html',
    'bible': 'workspace_shell.html',
}


def htmx_base(request):
    """
    Returns 'base_partial.html' if it's an HTMX request, otherwise 'base.html'.
    Also injects shell_template: the correct workspace shell for the current
    site (learn.ichebo.org / bible.ichebo.org get lean participant shells;
    everything else gets the full agency workspace_shell.html).
    """
    site = getattr(request, 'site', 'agency')
    shell = _SUBDOMAIN_SHELLS.get(site, 'workspace_shell.html')

    if request.headers.get('HX-Request'):
        return {'base_template': 'base_partial.html', 'shell_template': shell}
    return {'base_template': 'base.html', 'shell_template': shell}
