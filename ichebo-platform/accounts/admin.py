from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'display_name', 'competence_level', 'status', 'induction_pathway', 'created_at')
    list_filter = ('status', 'competence_level', 'induction_pathway')
    search_fields = ('email', 'display_name')
    ordering = ('-created_at',)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Formation', {'fields': ('competence_level', 'status', 'induction_pathway', 'induction_enrolled_at', 'induction_completed_at')}),
        ('Preferences', {'fields': ('display_name', 'avatar', 'preferences', 'fcm_token', 'preferred_bible_translation')}),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'member_number', 'country', 'occupation', 'terms_accepted', 'created_at')
    list_filter = ('country', 'gender', 'marital_status', 'accepted_christ', 'church_member', 'terms_accepted')
    search_fields = ('user__email', 'full_name', 'member_number', 'phone_number')
    readonly_fields = ('member_number', 'created_at', 'updated_at')
    fieldsets = (
        ('Identity', {'fields': ('user', 'title', 'full_name', 'phone_number', 'date_of_birth', 'gender', 'marital_status', 'member_number')}),
        ('Location', {'fields': ('address', 'country')}),
        ('Secure', {'fields': ('id_number',), 'classes': ('collapse',)}),
        ('Qualifications & Gifts', {'fields': ('occupation', 'education', 'interests', 'gifts_skills')}),
        ('Existing Christian', {'fields': ('accepted_christ', 'church_member', 'church_name', 'referee_1_name', 'referee_2_name', 'referee_letter_1', 'referee_letter_2')}),
        ('Consent', {'fields': ('terms_accepted', 'terms_accepted_at')}),
        ('Bio', {'fields': ('bio',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
