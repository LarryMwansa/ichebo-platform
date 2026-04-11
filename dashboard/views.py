from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from paraclete.service import build_digest


@login_required
def index(request):
    digest = build_digest(request.user)
    return render(request, 'dashboard/index.html', {'digest': digest})
