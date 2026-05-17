from django.urls import path
from . import template_views

app_name = 'tenants'

urlpatterns = [
    # Steward dashboard (replaces my_tenants as primary steward surface)
    path('steward/',                                          template_views.steward_dashboard,   name='steward-dashboard'),
    # Member view (non-stewards, all users)
    path('',                                                  template_views.my_tenants,           name='my-tenants'),
    # Tenant CRUD
    path('create/',                                           template_views.create_tenant,        name='create-tenant'),
    path('<uuid:tenant_id>/created/',                         template_views.tenant_created,       name='tenant-created'),
    # Tenant detail + member management
    path('<uuid:tenant_id>/',                                 template_views.tenant_detail,        name='tenant-detail'),
    path('<uuid:tenant_id>/invite/',                          template_views.invite_member,        name='invite-member'),
    path('<uuid:tenant_id>/members/<uuid:perm_id>/role/',     template_views.assign_member_role,   name='assign-member-role'),
    path('<uuid:tenant_id>/members/<uuid:perm_id>/remove/',   template_views.remove_member_view,   name='remove-member'),
    # Invitation accept (public — token auth)
    path('invite/accept/<str:token>/',                        template_views.invitation_accept,    name='invitation-accept'),
]
