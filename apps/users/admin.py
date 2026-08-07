from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Tenant & Role Information', {
            'fields': (
                'role', 
                'institution', 
                'phone', 
                'designation', 
                'is_approved', 
                'assigned_competitions', 
                'assigned_programs'
            )
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Tenant & Role Information', {
            'fields': (
                'email', 
                'role', 
                'institution', 
                'phone', 
                'designation', 
                'is_approved'
            )
        }),
    )
    list_display = ('username', 'email', 'role', 'institution', 'is_approved', 'is_staff', 'is_superuser')
    list_filter = ('role', 'is_approved', 'institution', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'designation')
    filter_horizontal = ('assigned_competitions', 'assigned_programs', 'groups', 'user_permissions')
