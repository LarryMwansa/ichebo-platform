def htmx_base(request):
    """
    Returns 'base_partial.html' if it's an HTMX request, otherwise 'base.html'.
    This allows templates to dynamically extend the right shell.
    """
    if request.headers.get('HX-Request'):
        return {'base_template': 'base_partial.html'}
    return {'base_template': 'base.html'}
