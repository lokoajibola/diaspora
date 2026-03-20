from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['phone_number', 'role', 'country', 'is_staff', 'is_active']
    list_filter = ['role', 'country', 'is_staff', 'is_active']
    
    # This fixes the "Unknown field username" error
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'country')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Role Information', {'fields': ('role',)}),
    )
    
    # This fixes the error when clicking "Add User"
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'password', 'role', 'country', 'is_staff', 'is_active'),
        }),
    )
    
    search_fields = ('phone_number',)
    ordering = ('phone_number',)

admin.site.register(User, CustomUserAdmin)