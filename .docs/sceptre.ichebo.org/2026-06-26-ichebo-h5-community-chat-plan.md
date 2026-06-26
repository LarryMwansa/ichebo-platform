# Phase H.5 — Community Chat / Intranet

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a tenant-scoped community noticeboard with member responses — posts visible to all tenant members, flat comments, steward-moderated. No real-time, no WebSockets, no threading.

**Architecture:** `community_post` and `community_comment` as `record_type` values on the existing `Record` model (ADR-003). No new models. No migrations beyond a `NOTIFICATION_TYPES` addition. HTMX for form submissions. Steward moderation via existing `status` lifecycle (`draft` → `active`). Comments use `custom_fields.parent_post_id` to associate with a post. Scoped to tenant — no cross-community visibility.

**Tech Stack:** Django 4.2, HTMX, existing `community`, `notifications`, `records` apps.

**Reference:** DOC J Part 7 — locked spec. `2026-06-25-ichebo-sceptre-system-design_doc-j_v1_0.md` is authoritative.

**Branch:** `v3-h5-community-chat` (cut from `main` after H.4 merges)

**Commit on completion:** `feat(community): H.5 — tenant-scoped community noticeboard with member responses`

---

## Pre-Flight Checks

```bash
git checkout main && git pull
git log --oneline main | grep "H.4"
# Expected: H.4 merge commit present

git checkout -b v3-h5-community-chat
source venv/bin/activate
python manage.py check
```

---

## Task 1 — Add community_post_created notification type

**Files:**
- Modify: `notifications/models.py`
- Create migration

**Step 1: Add to NOTIFICATION_TYPES**

```python
('community_post_created', 'Community Post Created'),
```

**Step 2: Add notify function to notifications/service.py**

```python
def notify_community_post_created(record):
    """
    Notify all active tenant members when a new community post goes active.
    Batched — one notification per member, not per steward.
    """
    from tenants.models import UserPermission

    member_user_ids = UserPermission.objects.filter(
        tenant=record.tenant,
        is_active=True,
    ).exclude(
        user=record.created_by,
    ).values_list('user_id', flat=True).distinct()

    from django.contrib.auth import get_user_model
    User = get_user_model()

    for user in User.objects.filter(id__in=member_user_ids):
        create_notification(
            user=user,
            notification_type='community_post_created',
            source_app='community',
            source_record_id=record.id,
            message=f'New post: {record.title}',
        )
```

**Step 3: Generate migration and apply**

```bash
python manage.py makemigrations notifications --name add_community_post_notification_type
python manage.py migrate
```

**Step 4: Verify**

```bash
python manage.py shell -c "
from notifications.models import Notification
from notifications.service import notify_community_post_created
assert 'community_post_created' in dict(Notification.NOTIFICATION_TYPES)
print('OK')
"
```

**Step 5: Commit**

```bash
git add notifications/models.py notifications/service.py notifications/migrations/
git commit -m "feat(notifications): add community_post_created notification type"
```

---

## Task 2 — Wire signal for community_post activation

**Files:**
- Modify: `notifications/signals.py`

**Context:** Notify tenant members when a `community_post` transitions to `status='active'`. Do not notify on `draft` creation — stewards must activate first.

**Step 1: Add signal handler**

```python
@receiver(post_save, sender=Record)
def handle_community_post_record(sender, instance, created, **kwargs):
    """
    Fire community post notification when status transitions to active.
    Only for record_type='community_post'.
    """
    if instance.record_type != 'community_post':
        return
    if created:
        return  # draft created — do not notify yet
    if instance.status == 'active':
        from notifications.service import notify_community_post_created
        notify_community_post_created(instance)
```

**Step 2: Verify**

```bash
python manage.py shell -c "
from notifications import signals
print('OK — signals module loads')
"
```

**Step 3: Commit**

```bash
git add notifications/signals.py
git commit -m "feat(notifications): wire post_save signal for community_post activation"
```

---

## Task 3 — Add community feed view (post list)

**Files:**
- Modify: `community/views.py`
- Modify: `community/urls.py`
- Create: `templates/community/community_feed.html`

**Step 1: Add view**

```python
@login_required
def community_feed(request):
    """
    Tenant-scoped community noticeboard.
    Shows all active community_post records for the member's tenant.
    Members see active posts. Stewards see draft + active.
    """
    from records.models import Record
    from tenants.models import UserPermission

    tenant = _get_active_community_tenant(request.user)
    if not tenant:
        return HttpResponseForbidden('No active community found.')

    user = request.user
    is_steward = (
        getattr(user, 'competence_level', '0') in ['3', '4', '5'] or
        UserPermission.objects.filter(
            user=user, role__endswith='-steward', is_active=True
        ).exists()
    )

    qs = Record.objects.filter(
        record_family='community',
        record_type='community_post',
        tenant=tenant,
        deleted_at__isnull=True,
    ).order_by('-created_at')

    if not is_steward:
        qs = qs.filter(status='active')
    # Stewards see draft + active

    return render(request, 'community/community_feed.html', {
        'posts': qs,
        'is_steward': is_steward,
    })
```

**Step 2: Add URL**

```python
path('feed/', views.community_feed, name='community_feed'),
```

**Step 3: Create template**

```html
<!-- templates/community/community_feed.html -->
{% extends "base.html" %}
{% block title %}Community{% endblock %}

{% block content %}
<div class="page-container">

  <div class="page-header">
    <span class="label-tag">&mdash;&mdash; COMMUNITY</span>
    <h1 class="page-title">Noticeboard</h1>
  </div>

  {% if is_steward %}
    <div class="page-actions">
      <a href="{% url 'community:community_post_new' %}" class="btn btn-primary">
        New Post
      </a>
    </div>
  {% endif %}

  {% if not posts %}
    <div class="empty-state">
      <p>No posts yet.</p>
    </div>
  {% else %}
    <div class="feed">
      {% for post in posts %}
        <div class="feed-item {% if post.status == 'draft' %}feed-item--draft{% endif %}">
          <div class="feed-item__left-rule"></div>
          <div class="feed-item__body">
            {% if post.status == 'draft' %}
              <span class="draft-badge">Draft</span>
            {% endif %}
            <h2 class="feed-item__title">
              <a href="{% url 'community:community_post_detail' post.id %}">{{ post.title }}</a>
            </h2>
            <p class="feed-item__excerpt">{{ post.content|truncatewords:40 }}</p>
            <div class="feed-item__meta">
              {{ post.created_by.get_full_name|default:post.created_by.username }}
              &middot; {{ post.created_at|date:"d M Y" }}
            </div>
          </div>
        </div>
      {% endfor %}
    </div>
  {% endif %}

</div>
{% endblock %}
```

**Step 4: Verify**

```bash
python manage.py check
python manage.py shell -c "
from django.urls import reverse
print(reverse('community:community_feed'))
print('OK')
"
```

**Step 5: Commit**

```bash
git add community/views.py community/urls.py templates/community/community_feed.html
git commit -m "feat(community): add tenant-scoped community feed view"
```

---

## Task 4 — Add post detail view with flat comments

**Files:**
- Modify: `community/views.py`
- Modify: `community/urls.py`
- Create: `templates/community/community_post_detail.html`

**Step 1: Add post detail view**

```python
@login_required
def community_post_detail(request, post_id):
    """
    Post detail — full content + flat comment list + comment form.
    """
    from records.models import Record
    import uuid

    tenant = _get_active_community_tenant(request.user)
    if not tenant:
        return HttpResponseForbidden()

    post = get_object_or_404(
        Record,
        id=post_id,
        record_family='community',
        record_type='community_post',
        tenant=tenant,
        deleted_at__isnull=True,
    )

    # Members can only see active posts
    from tenants.models import UserPermission
    is_steward = (
        getattr(request.user, 'competence_level', '0') in ['3', '4', '5'] or
        UserPermission.objects.filter(
            user=request.user, role__endswith='-steward', is_active=True
        ).exists()
    )
    if post.status != 'active' and not is_steward:
        raise Http404

    comments = Record.objects.filter(
        record_family='community',
        record_type='community_comment',
        tenant=tenant,
        status='active',
        deleted_at__isnull=True,
        custom_fields__parent_post_id=str(post_id),
    ).order_by('created_at')

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Record.objects.create(
                id=uuid.uuid4(),
                record_class='organizational',
                record_family='community',
                record_type='community_comment',
                title='comment',
                content=content,
                status='active',
                tenant=tenant,
                created_by=request.user,
                custom_fields={'parent_post_id': str(post_id)},
                permissions_data={'visibility': 'tenant'},
            )
            return redirect('community:community_post_detail', post_id=post_id)

    return render(request, 'community/community_post_detail.html', {
        'post': post,
        'comments': comments,
        'is_steward': is_steward,
    })
```

**Step 2: Add URL**

```python
path('feed/<uuid:post_id>/', views.community_post_detail, name='community_post_detail'),
```

**Step 3: Create template**

```html
<!-- templates/community/community_post_detail.html -->
{% extends "base.html" %}
{% block title %}{{ post.title }}{% endblock %}

{% block content %}
<div class="page-container">

  <a href="{% url 'community:community_feed' %}" class="back-link">
    &larr; Community
  </a>

  <div class="post-detail">
    <div class="post-detail__header">
      <span class="label-tag">&mdash;&mdash; COMMUNITY POST</span>
      <h1 class="post-detail__title">{{ post.title }}</h1>
      <div class="post-detail__meta">
        {{ post.created_by.get_full_name|default:post.created_by.username }}
        &middot; {{ post.created_at|date:"d M Y" }}
      </div>
    </div>

    <div class="post-detail__content">
      {{ post.content|linebreaks }}
    </div>
  </div>

  <div class="comments-section">
    <h2 class="comments-section__title">
      Responses ({{ comments.count }})
    </h2>

    {% for comment in comments %}
      <div class="comment-item">
        <div class="comment-item__author">
          {{ comment.created_by.get_full_name|default:comment.created_by.username }}
          <span class="comment-item__date">{{ comment.created_at|date:"d M Y" }}</span>
        </div>
        <div class="comment-item__content">{{ comment.content|linebreaks }}</div>
      </div>
    {% empty %}
      <p class="empty-state-inline">No responses yet. Be the first.</p>
    {% endfor %}

    <div class="comment-form">
      <form method="post"
            hx-post="{% url 'community:community_post_detail' post.id %}"
            hx-target=".comments-section"
            hx-swap="outerHTML">
        {% csrf_token %}
        <div class="field-group">
          <label for="id_comment_content" class="field-label">Add a response</label>
          <textarea id="id_comment_content"
                    name="content"
                    rows="3"
                    placeholder="Share your response..."
                    class="field-input"
                    required></textarea>
        </div>
        <button type="submit" class="btn btn-primary">Post Response</button>
      </form>
    </div>
  </div>

</div>
{% endblock %}
```

**Step 4: Commit**

```bash
git add community/views.py community/urls.py templates/community/community_post_detail.html
git commit -m "feat(community): add post detail view with flat comment form"
```

---

## Task 5 — Add steward post creation and moderation views

**Files:**
- Modify: `community/views.py`
- Modify: `community/urls.py`
- Create: `templates/community/community_post_new.html`
- Create: `templates/community/community_moderation_queue.html`

**Step 1: Add post creation view (steward only)**

```python
@login_required
def community_post_new(request):
    """
    Steward creates a new community post.
    Created as draft — must be activated to become visible.
    """
    import uuid
    from tenants.models import UserPermission

    user = request.user
    level_ok = getattr(user, 'competence_level', '0') in ['3', '4', '5']
    role_ok = UserPermission.objects.filter(
        user=user, role__endswith='-steward', is_active=True
    ).exists()
    if not (level_ok or role_ok):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    tenant = _get_active_community_tenant(user)
    if not tenant:
        return HttpResponseForbidden()

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        publish_now = request.POST.get('publish_now') == '1'

        if not title or not content:
            return render(request, 'community/community_post_new.html', {
                'error': 'Title and content are required.',
                'title': title,
                'content': content,
            })

        record = Record.objects.create(
            id=uuid.uuid4(),
            record_class='organizational',
            record_family='community',
            record_type='community_post',
            title=title,
            content=content,
            status='active' if publish_now else 'draft',
            tenant=tenant,
            created_by=user,
            custom_fields={},
            permissions_data={'visibility': 'tenant'},
        )
        # Signal fires for notify if published immediately
        return redirect('community:community_feed')

    return render(request, 'community/community_post_new.html', {
        'error': None, 'title': '', 'content': '',
    })


@login_required
def community_post_activate(request, post_id):
    """
    Steward activates a draft post — transitions draft → active.
    POST only.
    """
    from tenants.models import UserPermission
    from records.models import Record

    user = request.user
    level_ok = getattr(user, 'competence_level', '0') in ['3', '4', '5']
    role_ok = UserPermission.objects.filter(
        user=user, role__endswith='-steward', is_active=True
    ).exists()
    if not (level_ok or role_ok):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    post = get_object_or_404(
        Record,
        id=post_id,
        record_family='community',
        record_type='community_post',
        status='draft',
        deleted_at__isnull=True,
    )

    if request.method == 'POST':
        post.status = 'active'
        post.save()
        # Signal fires — notify_community_post_created dispatched
    return redirect('community:community_feed')
```

**Step 2: Add URLs**

```python
path('feed/new/', views.community_post_new, name='community_post_new'),
path('feed/<uuid:post_id>/activate/', views.community_post_activate, name='community_post_activate'),
```

**Step 3: Create new post template**

```html
<!-- templates/community/community_post_new.html -->
{% extends "base.html" %}
{% block title %}New Post{% endblock %}

{% block content %}
<div class="page-container">
  <div class="page-header">
    <span class="label-tag">&mdash;&mdash; COMMUNITY</span>
    <h1 class="page-title">New Post</h1>
  </div>

  {% if error %}
    <div class="form-error">{{ error }}</div>
  {% endif %}

  <form method="post">
    {% csrf_token %}
    <div class="field-group">
      <label for="id_title" class="field-label">Title</label>
      <input type="text" id="id_title" name="title"
             value="{{ title }}" maxlength="255" required class="field-input">
    </div>
    <div class="field-group">
      <label for="id_content" class="field-label">Content</label>
      <textarea id="id_content" name="content" rows="8"
                required class="field-input">{{ content }}</textarea>
    </div>
    <div class="form-actions">
      <button type="submit" name="publish_now" value="0" class="btn btn-secondary">
        Save as Draft
      </button>
      <button type="submit" name="publish_now" value="1" class="btn btn-primary">
        Publish Now
      </button>
    </div>
  </form>
</div>
{% endblock %}
```

**Step 4: Commit**

```bash
git add community/views.py community/urls.py \
  templates/community/community_post_new.html
git commit -m "feat(community): add steward post creation and activation views"
```

---

## Task 6 — Write tests

**Files:**
- Create: `community/tests/test_community_chat.py`

```python
# community/tests/test_community_chat.py
"""
Tests for Phase H.5 — Community Chat / Intranet.
"""
import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from records.models import Record
from tenants.models import Tenant, UserPermission

User = get_user_model()


def make_tenant(name='Chat Tenant', path='/global/chat/'):
    return Tenant.objects.create(name=name, tenant_path=path)


def make_user(username, level='1', tenant=None, role=None):
    user = User.objects.create_user(
        username=username, password='testpass123',
        email=f'{username}@test.com',
    )
    user.competence_level = level
    user.save()
    if tenant and role:
        UserPermission.objects.create(
            user=user, tenant=tenant, role=role,
            is_active=True, tenant_path=tenant.tenant_path,
        )
    return user


def make_post(tenant, author, status='active', title='Test Post'):
    return Record.objects.create(
        id=uuid.uuid4(),
        record_class='organizational',
        record_family='community',
        record_type='community_post',
        title=title,
        content='Post content here.',
        status=status,
        tenant=tenant,
        created_by=author,
        custom_fields={},
        permissions_data={'visibility': 'tenant'},
    )


class TestCommunityFeed(TestCase):

    def setUp(self):
        self.tenant = make_tenant()
        self.member = make_user('chat_member', level='1', tenant=self.tenant, role='member')
        self.steward = make_user('chat_steward', level='3', tenant=self.tenant, role='branch-steward')
        self.client = Client()

    def test_member_sees_active_posts(self):
        make_post(self.tenant, self.steward, status='active', title='Active Post')
        self.client.login(username='chat_member', password='testpass123')
        response = self.client.get(reverse('community:community_feed'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Active Post')

    def test_member_does_not_see_draft_posts(self):
        make_post(self.tenant, self.steward, status='draft', title='Draft Post')
        self.client.login(username='chat_member', password='testpass123')
        response = self.client.get(reverse('community:community_feed'))
        self.assertNotContains(response, 'Draft Post')

    def test_steward_sees_draft_posts(self):
        make_post(self.tenant, self.steward, status='draft', title='Draft Post')
        self.client.login(username='chat_steward', password='testpass123')
        response = self.client.get(reverse('community:community_feed'))
        self.assertContains(response, 'Draft Post')

    def test_feed_requires_login(self):
        response = self.client.get(reverse('community:community_feed'))
        self.assertEqual(response.status_code, 302)


class TestPostCreation(TestCase):

    def setUp(self):
        self.tenant = make_tenant(name='Chat T2', path='/global/chat2/')
        self.steward = make_user('chat_stew2', level='3', tenant=self.tenant, role='branch-steward')
        self.member = make_user('chat_mem2', level='1', tenant=self.tenant, role='member')
        self.client = Client()

    def test_steward_can_create_draft_post(self):
        self.client.login(username='chat_stew2', password='testpass123')
        self.client.post(reverse('community:community_post_new'), {
            'title': 'New Draft',
            'content': 'Draft content.',
            'publish_now': '0',
        })
        post = Record.objects.get(record_type='community_post', title='New Draft')
        self.assertEqual(post.status, 'draft')

    def test_steward_can_publish_immediately(self):
        self.client.login(username='chat_stew2', password='testpass123')
        self.client.post(reverse('community:community_post_new'), {
            'title': 'Published Post',
            'content': 'Published content.',
            'publish_now': '1',
        })
        post = Record.objects.get(record_type='community_post', title='Published Post')
        self.assertEqual(post.status, 'active')

    def test_member_cannot_create_post(self):
        self.client.login(username='chat_mem2', password='testpass123')
        response = self.client.get(reverse('community:community_post_new'))
        self.assertEqual(response.status_code, 403)

    def test_steward_can_activate_draft(self):
        post = make_post(self.tenant, self.steward, status='draft')
        self.client.login(username='chat_stew2', password='testpass123')
        self.client.post(reverse('community:community_post_activate', args=[post.id]))
        post.refresh_from_db()
        self.assertEqual(post.status, 'active')


class TestComments(TestCase):

    def setUp(self):
        self.tenant = make_tenant(name='Chat T3', path='/global/chat3/')
        self.member = make_user('chat_mem3', level='1', tenant=self.tenant, role='member')
        self.steward = make_user('chat_stew3', level='3', tenant=self.tenant, role='branch-steward')
        self.post = make_post(self.tenant, self.steward, status='active')
        self.client = Client()

    def test_member_can_comment(self):
        self.client.login(username='chat_mem3', password='testpass123')
        url = reverse('community:community_post_detail', args=[self.post.id])
        self.client.post(url, {'content': 'My response here.'})
        comment = Record.objects.get(record_type='community_comment')
        self.assertEqual(comment.content, 'My response here.')
        self.assertEqual(comment.custom_fields['parent_post_id'], str(self.post.id))
        self.assertEqual(comment.status, 'active')

    def test_comments_scoped_to_post(self):
        self.client.login(username='chat_mem3', password='testpass123')
        url = reverse('community:community_post_detail', args=[self.post.id])
        self.client.post(url, {'content': 'Comment on this post.'})

        other_post = make_post(self.tenant, self.steward, status='active', title='Other')
        response = self.client.get(
            reverse('community:community_post_detail', args=[other_post.id])
        )
        self.assertNotContains(response, 'Comment on this post.')

    def test_member_cannot_see_draft_post_detail(self):
        draft = make_post(self.tenant, self.steward, status='draft', title='Hidden')
        self.client.login(username='chat_mem3', password='testpass123')
        url = reverse('community:community_post_detail', args=[draft.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
```

**Run tests:**

```bash
python manage.py test community.tests.test_community_chat -v 2
python manage.py test --verbosity=1 2>&1 | tail -5
```

**Commit:**

```bash
git add community/tests/test_community_chat.py
git commit -m "test(community): H.5 community chat / noticeboard test suite"
```

---

## Task 7 — Final verification and merge

```bash
python manage.py check
python manage.py showmigrations | grep "\[ \]"

git log --oneline main..HEAD
# 7 commits expected

git checkout main
git merge --no-ff v3-h5-community-chat \
  -m "feat(community): H.5 — tenant-scoped community noticeboard with member responses"
git push origin main
```

---

## Exit Criteria

- [ ] Members see only `active` posts; stewards see `draft` + `active`
- [ ] Steward can create a post as draft or publish immediately
- [ ] Steward can activate a draft post — notification fires to tenant members
- [ ] Members can post flat comments on active posts
- [ ] Comments scoped to their parent post — no cross-post bleed
- [ ] Members cannot access draft post detail (404)
- [ ] Members cannot access post creation view (403)
- [ ] `python manage.py check` — 0 issues
- [ ] No new models, no migrations to Tenant/UserPermission/Activity
