from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views import View
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response


# ---------------------------------------------------------------------------
# API views (stub — no Notification model in MVP)
# ---------------------------------------------------------------------------

@api_view(['GET'])
def notification_list(request):
    """Returns an empty paginated list. Shape is stable for post-MVP drop-in."""
    return Response({
        'count': 0,
        'next': None,
        'previous': None,
        'results': [],
    })


@api_view(['GET'])
def unread_count(request):
    return Response({'count': 0})


def htmx_unread_badge(request):
    """
    HTMX endpoint — returns badge HTML.
    Count is 0 in MVP so badge is always hidden (display:none).
    Post-MVP: swap this with real query and show badge when count > 0.
    """
    count = 0
    if count > 0:
        html = (
            f'<span id="notif-badge" style="display:flex;position:absolute;top:-4px;right:-4px;'
            f'background:var(--primary);color:#fff;border-radius:50%;width:16px;height:16px;'
            f'font-size:10px;font-weight:700;align-items:center;justify-content:center;">'
            f'{count}</span>'
        )
    else:
        html = '<span id="notif-badge" style="display:none;"></span>'
    return HttpResponse(html)


@api_view(['POST'])
def mark_all_read(request):
    """Stub — no effect in MVP."""
    return Response({'marked': 0})


@api_view(['GET'])
def health(request):
    return Response({'status': 'ok'})


# ---------------------------------------------------------------------------
# Template view
# ---------------------------------------------------------------------------

class NotificationListView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'notifications/notifications.html')
