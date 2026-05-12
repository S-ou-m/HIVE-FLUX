from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Role, UserRole, Permission, RolePermission, Faculty, Student

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'college', 'is_staff', 'is_active', 'is_deleted')
    fieldsets = UserAdmin.fieldsets + (
        ('College Info', {'fields': ('college', 'is_deleted')}),
    )

admin.site.register(Role)
admin.site.register(UserRole)
admin.site.register(Permission)
admin.site.register(RolePermission)
admin.site.register(Faculty)
admin.site.register(Student)
