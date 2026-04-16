from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views import View
from django.shortcuts import render
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


# ---------------------------------------------------------------------------
# API views
# ---------------------------------------------------------------------------

@api_view(['GET'])
def notification_list(request):
    """Paginated list of the authenticated user's notifications, newest first."""
    qs = Notification.objects.filter(user=request.user).order_by('-created_at')

    # Simple manual pagination matching the existing stub shape
    page_size = 20
    page = max(int(request.GET.get('page', 1)), 1)
    offset = (page - 1) * page_size
    total = qs.count()
    items = qs[offset:offset + page_size]

    return Response({
        'count': total,
        'next': None if offset + page_size >= total else page + 1,
        'previous': None if page <= 1 else page - 1,
        'results': NotificationSerializer(items, many=True).data,
    })


@api_view(['GET'])
def unread_count(request):
    count = Notification.objects.filter(user=request.user, read_at__isnull=True).count()
    return Response({'count': count})


@login_required
def htmx_unread_badge(request):
    """
    HTMX endpoint — returns badge HTML fragment.
    Polled from base.html every 60 s via hx-trigger="load, every 60s".
    """
    count = Notification.objects.filter(
        user=request.user, read_at__isnull=True
    ).count()

    if count > 0:
        display_count = count if count < 100 else '99+'
        html = (
            f'<span id="notif-badge" style="display:flex;position:absolute;top:-4px;right:-4px;'
            f'background:var(--primary);color:#fff;border-radius:50%;min-width:16px;height:16px;'
            f'font-size:10px;font-weight:700;align-items:center;justify-content:center;'
            f'padding:0 3px;">'
            f'{display_count}</span>'
        )
    else:
        html = '<span id="notif-badge" style="display:none;"></span>'

    return HttpResponse(html)


@api_view(['POST'])
def mark_all_read(request):
    """Mark all unread notifications as read for the current user."""
    now = timezone.now()
    marked = Notification.objects.filter(
        user=request.user,
        read_at__isnull=True,
    ).update(read_at=now)
    return Response({'marked': marked})


@api_view(['POST'])
def mark_one_read(request, notification_id):
    """Mark a single notification as read."""
    try:
        n = Notification.objects.get(id=notification_id, user=request.user)
        n.mark_read()
        return Response({'status': 'ok'})
    except Notification.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)


@api_view(['GET'])
def health(request):
    return Response({'status': 'ok'})


# ---------------------------------------------------------------------------
# Template view
# ---------------------------------------------------------------------------

class NotificationListView(LoginRequiredMixin, View):
    def get(self, request):
        notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:50]
        unread = sum(1 for n in notifications if not n.is_read)
        return render(request, 'notifications/notifications.html', {
            'notifications': notifications,
            'unread_count': unread,
        })
