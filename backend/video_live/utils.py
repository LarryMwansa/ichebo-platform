import re


def get_embed_type(url):
    """Return 'youtube', 'vimeo', 'mp4', or 'unknown'."""
    if not url:
        return 'unknown'
    u = url.strip()
    if re.search(r'(youtube\.com|youtu\.be)', u):
        return 'youtube'
    if 'vimeo.com' in u:
        return 'vimeo'
    if u.lower().endswith('.mp4') or 'video/mp4' in u:
        return 'mp4'
    return 'unknown'


def get_youtube_id(url):
    patterns = [
        r'youtu\.be/([^?&]+)',
        r'youtube\.com/watch\?v=([^&]+)',
        r'youtube\.com/embed/([^?&]+)',
        r'youtube\.com/live/([^?&]+)',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def get_vimeo_id(url):
    m = re.search(r'vimeo\.com/(\d+)', url)
    return m.group(1) if m else None


def get_embed_url(url):
    """Convert a raw video URL to its embeddable form."""
    kind = get_embed_type(url)
    if kind == 'youtube':
        vid = get_youtube_id(url)
        if vid:
            return f'https://www.youtube.com/embed/{vid}?autoplay=0&rel=0'
    if kind == 'vimeo':
        vid = get_vimeo_id(url)
        if vid:
            return f'https://player.vimeo.com/video/{vid}'
    return url  # mp4 and unknown: return as-is
