from django.contrib import admin
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User 

class CustomUserAdmin(UserAdmin):
    model = User
    # What fields show up in the admin list
    list_display = ("email", "username", "age", "isauthor", "country", "is_staff", "is_active")
    list_filter = ("isauthor", "country", "is_staff", "is_active")

    # Fieldsets control the detail page layout
    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Personal Info", {"fields": ("age", "country", "isauthor")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )

    # Fields used when creating a new user via admin
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2", "age", "country", "isauthor", "is_staff", "is_active"),
        }),
    )

    search_fields = ("email", "username")
    ordering = ("email",)

admin.site.register(User, CustomUserAdmin)
# Register your models here.
