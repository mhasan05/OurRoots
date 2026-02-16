from django.contrib import admin
from django.utils.html import format_html
from .models import (
    AudioCategory,
    AudioGuide,
    AudioGuideDownload,
    AudioGuideProgress,
)


# -----------------------------
# Inline Models
# -----------------------------

class AudioGuideInline(admin.TabularInline):
    model = AudioGuide
    extra = 0
    fields = (
        "title",
        "is_active",
        "is_featured",
        "duration_seconds",
        "sort_order",
    )
    show_change_link = True


class AudioGuideProgressInline(admin.TabularInline):
    model = AudioGuideProgress
    extra = 0
    readonly_fields = ("user", "position_seconds", "is_completed", "updated_at")
    can_delete = False


class AudioGuideDownloadInline(admin.TabularInline):
    model = AudioGuideDownload
    extra = 0
    readonly_fields = ("user", "downloaded_at")
    can_delete = False


# -----------------------------
# Category Admin
# -----------------------------

@admin.register(AudioCategory)
class AudioCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "slug",
        "is_active",
        "sort_order",
        "guides_count",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    ordering = ("sort_order", "id")

    inlines = [AudioGuideInline]

    def guides_count(self, obj):
        return obj.guides.count()
    guides_count.short_description = "Guides"


# -----------------------------
# Audio Guide Admin
# -----------------------------

@admin.register(AudioGuide)
class AudioGuideAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "category",
        "duration_mmss_display",
        "is_featured",
        "is_active",
        "downloads_count",
        "sort_order",
    )
    list_filter = (
        "is_active",
        "is_featured",
        "category",
        "created_at",
    )
    search_fields = ("title", "description")
    ordering = ("sort_order", "-created_at", "id")

    readonly_fields = (
        "duration_mmss_display",
        "created_at",
        "downloads_count",
    )

    fieldsets = (
        ("Basic Info", {
            "fields": (
                "title",
                "subtitle",
                "description",
                "category",
            )
        }),
        ("Media", {
            "fields": (
                "cover_image",
                "audio_file",
                "audio_url",
                "duration_seconds",
                "duration_mmss_display",
            )
        }),
        ("Settings", {
            "fields": (
                "is_featured",
                "is_active",
                "sort_order",
                "created_at",
                "downloads_count",
            )
        }),
    )

    inlines = [AudioGuideProgressInline, AudioGuideDownloadInline]

    def duration_mmss_display(self, obj):
        return obj.duration_mmss
    duration_mmss_display.short_description = "Duration (MM:SS)"

    def downloads_count(self, obj):
        return obj.downloads.count()
    downloads_count.short_description = "Downloads"


# -----------------------------
# Progress Admin
# -----------------------------

@admin.register(AudioGuideProgress)
class AudioGuideProgressAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "guide",
        "user",
        "position_seconds",
        "is_completed",
        "updated_at",
    )
    list_filter = ("is_completed", "updated_at")
    search_fields = ("guide__title", "user__email")
    ordering = ("-updated_at",)


# -----------------------------
# Download Admin
# -----------------------------

@admin.register(AudioGuideDownload)
class AudioGuideDownloadAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "guide",
        "user",
        "downloaded_at",
    )
    list_filter = ("downloaded_at",)
    search_fields = ("guide__title", "user__email")
    ordering = ("-downloaded_at",)
