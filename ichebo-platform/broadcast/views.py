import uuid
import datetime
import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt

from broadcast.models import ChannelConfig, ChannelSlot
from tenants.models import Tenant


def _require_architect(request):
    if getattr(request.user, 'competence_level', 0) < 5:
        raise PermissionDenied


@login_required
def channel_overview(request):
    _require_architect(request)

    tenant_id = request.GET.get('tenant_id')
    view_mode = request.GET.get('view', 'center')  # Default to Media Center Home Page
    tenants = Tenant.objects.filter(deleted_at__isnull=True).order_by('name')
    selected_tenant = None
    slots = []
    config = None
    videos = []

    if not tenant_id and tenants.exists():
        selected_tenant = tenants.first()
    elif tenant_id:
        selected_tenant = get_object_or_404(Tenant, id=tenant_id, deleted_at__isnull=True)

    if selected_tenant:
        from records.models import Record
        from media.models import VideoRecord
        
        if view_mode in ('library', 'center'):
            qs = Record.objects.filter(record_family='media', tenant=selected_tenant, deleted_at__isnull=True).order_by('-created_at')
            videos = [VideoRecord(r) for r in qs[:100]]
            
        slots = ChannelSlot.objects.filter(
            tenant=selected_tenant,
            deleted_at__isnull=True,
        ).order_by('scheduled_start')
        config = ChannelConfig.objects.filter(tenant=selected_tenant).first()

    return render(request, 'broadcast/channel_overview.html', {
        'tenants': tenants,
        'selected_tenant': selected_tenant,
        'view_mode': view_mode,
        'slots': slots,
        'config': config,
        'videos': videos,
        'now': timezone.now(),
        'active_app': 'channel',
        'ws_page_title': 'Media Center & Broadcasting',
        'media_engine_public_url': getattr(settings, 'MEDIA_ENGINE_PUBLIC_URL', 'https://video.ichebo.org'),
    })


@login_required
def channel_slot_add(request):
    _require_architect(request)

    tenants = Tenant.objects.filter(deleted_at__isnull=True).order_by('name')
    preselect_tenant_id = request.GET.get('tenant_id', '').strip()
    if not preselect_tenant_id and tenants.exists():
        preselect_tenant_id = str(tenants.first().id)

    errors = []
    data = {}

    if request.method == 'POST':
        data = request.POST
        tenant_id = data.get('tenant_id', '').strip()
        title = data.get('title', '').strip()
        content_type = data.get('content_type', 'vod')
        video_record_id_raw = data.get('video_record_id', '').strip()
        scheduled_start_raw = data.get('scheduled_start', '').strip()
        scheduled_end_raw = data.get('scheduled_end', '').strip()
        tz_offset = data.get('tz_offset_minutes', '0')

        if not tenant_id:
            errors.append('Community is required.')
        if not title:
            errors.append('Title is required.')
        if not scheduled_start_raw or not scheduled_end_raw:
            errors.append('Start and end times are required.')

        video_record_id = None
        if content_type == 'vod' and video_record_id_raw:
            try:
                video_record_id = uuid.UUID(video_record_id_raw)
            except ValueError:
                errors.append('Selected VOD video UUID is invalid.')

        if not errors:
            from community.views import _parse_local_datetime
            tenant = get_object_or_404(Tenant, id=tenant_id, deleted_at__isnull=True)
            start_dt = _parse_local_datetime(scheduled_start_raw, tz_offset)
            end_dt = _parse_local_datetime(scheduled_end_raw, tz_offset)

            if not start_dt or not end_dt:
                errors.append('Invalid date/time format.')
            elif end_dt <= start_dt:
                errors.append('End time must be after start time.')
            else:
                ChannelSlot.objects.create(
                    tenant=tenant,
                    title=title,
                    content_type=content_type,
                    video_record_id=video_record_id,
                    scheduled_start=start_dt,
                    scheduled_end=end_dt,
                    created_by=request.user,
                )
                return redirect(f'/channel/?view=scheduler&tenant_id={tenant_id}')

    return render(request, 'broadcast/channel_slot_form.html', {
        'tenants': tenants,
        'errors': errors,
        'data': data,
        'preselect_tenant_id': preselect_tenant_id,
        'active_app': 'channel',
        'ws_page_title': 'Add Channel Slot',
        'media_engine_public_url': getattr(settings, 'MEDIA_ENGINE_PUBLIC_URL', 'https://video.ichebo.org'),
    })


@login_required
def channel_slot_delete(request, slot_id):
    _require_architect(request)
    slot = get_object_or_404(ChannelSlot, id=slot_id, deleted_at__isnull=True)
    tenant_id = slot.tenant_id
    if request.method == 'POST':
        slot.soft_delete()
    return redirect(f'/channel/?tenant_id={tenant_id}')


@login_required
def channel_config_edit(request, tenant_id):
    _require_architect(request)
    tenant = get_object_or_404(Tenant, id=tenant_id, deleted_at__isnull=True)
    config, _ = ChannelConfig.objects.get_or_create(
        tenant=tenant,
        defaults={'created_by': request.user},
    )

    errors = []

    if request.method == 'POST':
        loop_default = request.POST.get('loop_default_video_id', '').strip()
        loop_external = request.POST.get('loop_default_external_url', '').strip()
        fallback_raw = request.POST.get('fallback_playlist', '').strip()

        fallback_list = [
            line.strip() for line in fallback_raw.splitlines() if line.strip()
        ]

        try:
            config.loop_default_video_id = uuid.UUID(loop_default) if loop_default else None
        except ValueError:
            errors.append('Loop default must be a valid UUID.')

        if not errors:
            config.loop_default_external_url = loop_external
            config.fallback_playlist = fallback_list
            config.save()
            return redirect(f'/channel/?tenant_id={tenant_id}')

    return render(request, 'broadcast/channel_config_form.html', {
        'tenant': tenant,
        'config': config,
        'fallback_playlist_text': '\n'.join(config.fallback_playlist),
        'errors': errors,
        'active_app': 'channel',
        'ws_page_title': f'Fallback Config — {tenant.name}',
        'media_engine_public_url': getattr(settings, 'MEDIA_ENGINE_PUBLIC_URL', 'https://video.ichebo.org'),
    })


@login_required
def channel_media_delete(request, record_id):
    _require_architect(request)
    if request.method == 'POST':
        from records.models import Record
        tenant_id = request.POST.get('tenant_id', '')
        record = get_object_or_404(Record, id=record_id, record_family='media', deleted_at__isnull=True)
        # Note: True hard delete vs soft delete. Records supports soft delete.
        record.soft_delete()
        
        # We redirect back to the library view
        url = '/channel/?view=library'
        if tenant_id:
            url += f'&tenant_id={tenant_id}'
        return redirect(url)
    return HttpResponseForbidden()
