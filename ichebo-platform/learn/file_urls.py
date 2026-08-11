"""
The gated lesson-file route, on its own so it can be mounted anywhere a
lesson is rendered.

Lessons appear on three surfaces — app.ichebo.org (learn.urls),
learn.ichebo.org (learn/subdomain_urls.py) and sceptre.ichebo.org — and the
attachments partial reverses {% url 'learn:lesson-file' %} on all of them.
Sceptre deliberately has no namespace of its own (see sceptre/urls.py), and
including the whole of learn.urls there would collide with its own learn/
routes, so this exposes just the one path under the 'learn' namespace.
"""
from django.urls import path

from learn import views

app_name = 'learn'

urlpatterns = [
    path('lesson-file/<uuid:attachment_id>/', views.lesson_file, name='lesson-file'),
]
