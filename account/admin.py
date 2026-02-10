from django.contrib import admin
from account.models import User
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group



class UserAuthAdmin(UserAdmin):
    list_display = (
        "id",
        "email",
        "full_name",
        "role",
        "is_active",
        "is_staff",
        "created_on",
    )

    list_filter = (
        "role",
        "is_active",
        "is_staff",
        "created_on",
    )

    search_fields = (
        "email",
        "full_name",
        "phone",
    )

    ordering = ("-created_on",)

    readonly_fields = (
        "created_on",
        "updated_on",
        "last_login",
    )

    fieldsets = (
        ("Basic Information", {
            "fields": (
                "full_name",
                "email",
                "phone",
                "image",
                "role",
            )
        }),
        ("Authentication", {
            "fields": (
                "password",
                "otp",
                "otp_expired_on",
            )
        }),
        ("Social Login", {
            "fields": (
                "google_id",
                "facebook_id",
                "apple_id",
            )
        }),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Metadata", {
            "fields": (
                "source",
                "heritage_connection",
                "created_on",
                "updated_on",
                "last_login",
            )
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "full_name",
                "email",
                "password1",
                "password2",
                "role",
                "is_active",
            ),
        }),
    )

admin.site.register(User,UserAuthAdmin)
admin.site.unregister(Group)
