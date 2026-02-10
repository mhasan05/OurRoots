from django.contrib import admin
from .models import *



class ProviderLanguageInline(admin.TabularInline):
    model = ProviderLanguage
    extra = 0


class ProviderSpecialtyInline(admin.TabularInline):
    model = ProviderSpecialty
    extra = 0


class ExperienceInline(admin.TabularInline):
    model = Experience
    extra = 0
    show_change_link = True


class ExperiencePackageInline(admin.TabularInline):
    model = ExperiencePackage
    extra = 0



@admin.register(CulturalProvider)
class CulturalProviderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "user",
        "country",
        "city",
        "is_verified",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_verified",
        "is_active",
        "country",
        "created_at",
    )

    search_fields = (
        "name",
        "bio",
        "contact_email",
        "user__email",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Basic Info", {
            "fields": (
                "user",
                "name",
                "tagline",
                "bio",
                "country",
                "city",
            )
        }),
        ("Contact Info", {
            "fields": (
                "contact_email",
                "contact_phone",
                "whatsapp_no",
                "website_url",
            )
        }),
        ("Status & Verification", {
            "fields": (
                "is_verified",
                "is_active",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    inlines = [
        ProviderLanguageInline,
        ProviderSpecialtyInline,
        ExperienceInline,
    ]



@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "provider",
        "location",
        "duration_hours",
        "base_price",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "location",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
        "provider__name",
    )

    ordering = ("-created_at",)

    readonly_fields = ("created_at",)

    inlines = [ExperiencePackageInline]



@admin.register(ExperiencePackage)
class ExperiencePackageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "package_name",
        "experience",
        "price",
        "max_people",
    )

    search_fields = (
        "package_name",
        "experience__title",
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "provider",
        "experience",
        "booking_date",
        "number_of_people",
        "total_amount",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "booking_date",
        "created_at",
    )

    search_fields = (
        "user__email",
        "provider__name",
        "experience__title",
    )

    ordering = ("-created_at",)

    readonly_fields = ("created_at",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "booking",
        "amount",
        "currency",
        "provider",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "currency",
        "provider",
        "created_at",
    )

    search_fields = (
        "booking__id",
    )

    readonly_fields = ("created_at",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "provider",
        "user",
        "rating",
        "created_at",
    )

    list_filter = (
        "rating",
        "created_at",
    )

    search_fields = (
        "provider__name",
        "user__email",
        "comment",
    )

    readonly_fields = ("created_at",)


@admin.register(ProviderStats)
class ProviderStatsAdmin(admin.ModelAdmin):
    list_display = (
        "provider",
        "total_bookings",
        "completed_bookings",
        "average_rating",
        "total_reviews",
        "last_updated",
    )

    readonly_fields = (
        "provider",
        "total_bookings",
        "completed_bookings",
        "average_rating",
        "total_reviews",
        "last_updated",
    )


