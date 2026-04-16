from django.urls import path
from . import api_views, views

app_name = 'community'

urlpatterns = [
    # ── My Community surface ─────────────────────────────────────────────────
    path('community/', views.my_community, name='community-home'),
    path('community/gatherings/', views.gatherings_list, name='community-gatherings'),

    # ── Steward management surface (Level 3+) — flat URLs ────────────────────
    path('community/management/', views.management_home, name='community-management'),
    path('community/members/', views.member_directory, name='community-members'),
    path('community/members/<uuid:member_id>/',
         views.member_profile, name='community-member-profile'),
    path('community/pipeline/', views.formation_pipeline, name='community-pipeline'),

    # ── Detail — must come after all fixed-string paths ──────────────────────
    path('community/<uuid:record_id>/', views.community_detail, name='community-detail'),

    # ── HTMX partials ────────────────────────────────────────────────────────
    path('community/htmx/announcement/create/',
         views.htmx_create_announcement, name='htmx-create-announcement'),
    path('community/htmx/announcement/<uuid:record_id>/archive/',
         views.htmx_archive_announcement, name='htmx-archive-announcement'),
    path('community/htmx/gathering/create/',
         views.htmx_create_gathering, name='htmx-create-gathering'),
    path('community/htmx/gathering/<uuid:record_id>/cancel/',
         views.htmx_cancel_gathering, name='htmx-cancel-gathering'),
    path('community/htmx/member/<uuid:permission_id>/shepherd/',
         views.htmx_set_shepherd, name='htmx-set-shepherd'),
    path('community/htmx/member/<uuid:permission_id>/order/',
         views.htmx_set_order, name='htmx-set-order'),
    path('community/htmx/member/<uuid:permission_id>/deactivate/',
         views.htmx_deactivate_member, name='htmx-deactivate-member'),
    path('community/htmx/members/search/',
         views.htmx_member_search, name='htmx-member-search'),
    path('community/htmx/announcements/',
         views.htmx_announcement_list, name='htmx-announcement-list'),
    path('community/htmx/gatherings/',
         views.htmx_gatherings_list, name='htmx-gatherings-list'),

    # ── Membership request flow ───────────────────────────────────────────────
    path('community/htmx/membership/request/',
         views.htmx_request_membership, name='htmx-membership-request'),
    path('community/htmx/membership/orientation-check/',
         views.htmx_orientation_check, name='htmx-orientation-check'),
    path('community/htmx/membership/pending/',
         views.htmx_pending_requests, name='htmx-pending-requests'),
    path('community/htmx/membership/<uuid:request_id>/review/',
         views.htmx_review_request, name='htmx-review-request'),
]
