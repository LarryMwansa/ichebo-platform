from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from records.models import Record
from media.models import VideoRecord

@login_required
def htmx_picker_grid(request):
    tenant_id = request.GET.get('tenant_id')
    mode = request.GET.get('mode', 'options_bar')  # options_bar | grid | list
    picker_context = request.GET.get('picker_context', 'generic')  # slot | loop | playlist | generic

    qs = Record.objects.filter(record_family='media', deleted_at__isnull=True).order_by('-created_at')
    
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)
        
    videos = [VideoRecord(r) for r in qs[:50]]
    
    return render(request, 'media/partials/_picker_grid.html', {
        'videos': videos,
        'mode': mode,
        'picker_context': picker_context,
        'tenant_id': tenant_id,
    })
