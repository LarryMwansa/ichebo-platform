import re


def get_embed_url(url):
    """
    Convert YouTube/Vimeo watch URLs to embeddable iframes.
    Returns direct URLs unchanged. Returns None for unrecognised input.
    """
    if not url or not isinstance(url, str):
        return None

    url = url.strip()

    # YouTube: youtube.com/watch?v=ID or youtu.be/ID
    yt = re.match(
        r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]+)',
        url
    )
    if yt:
        return f'https://www.youtube.com/embed/{yt.group(1)}?rel=0'

    # Vimeo: vimeo.com/ID
    vm = re.match(r'(?:https?://)?(?:www\.)?vimeo\.com/(\d+)', url)
    if vm:
        return f'https://player.vimeo.com/video/{vm.group(1)}'

    # HLS manifest or direct video file — return as-is
    if re.search(r'\.(m3u8|mp4|webm|ogg|mov)(\?.*)?$', url, re.IGNORECASE):
        return url

    # Unknown — return as-is and let the template decide
    return url


def get_video_type(url):
    """Return 'youtube', 'vimeo', 'hls', 'direct', or 'unknown'.

    'hls' (.m3u8) needs hls.js in every browser except Safari — see
    video/_player.html, which is the only template branching on this value.
    Checked before the generic file-extension branches since an HLS
    manifest is also matched by nothing else here, but keeping the check
    explicit (not folded into the direct-video regex) makes the two
    fundamentally different playback mechanisms (native <video> vs.
    hls.js-fed MediaSource) easy to find from this function alone.
    """
    if not url:
        return 'unknown'
    url = url.strip()
    if re.search(r'(?:youtube\.com|youtu\.be)', url):
        return 'youtube'
    if 'vimeo.com' in url:
        return 'vimeo'
    if re.search(r'\.m3u8(\?.*)?$', url, re.IGNORECASE):
        return 'hls'
    if re.search(r'\.(mp4|webm|ogg|mov)(\?.*)?$', url, re.IGNORECASE):
        return 'direct'
    return 'unknown'
