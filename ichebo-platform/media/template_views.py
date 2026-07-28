from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from records.models import Record
from media.models import VideoRecord

@login_required
def htmx_picker_grid(request):
    tenant_id = request.GET.get('tenant_id')
    qs = Record.objects.filter(record_family='media').order_by('-created_at')
    
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)
    else:
        # If no tenant is provided, perhaps show user's media? 
        # But per contract, all media is tenant_scoped or public. We'll just show them.
        pass
        
    videos = [VideoRecord(r) for r in qs[:50]]
    
    return render(request, 'media/partials/_picker_grid.html', {
        'videos': videos,
    })
