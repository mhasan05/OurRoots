from django.contrib import admin
from django.utils.html import format_html

from .models import (
    ContentCategory,
    ContentItem,
    ContentEnrollment,
    ContentBookmark,
    ContentRating,
)


# -----------------------------
# Inlines
# -----------------------------

class ContentItemInline(admin.TabularInline):
    model = ContentItem
    extra = 0
    fields = ("title", "content_type", "is_premium", "is_active", "sort_order")
    show_change_link = True


class EnrollmentInline(admin.TabularInline):
    model = ContentEnrollment
    extra = 0
    readonly_fields = ("user", "created_at")
    can_delete = False


class BookmarkInline(admin.TabularInline):
    model = ContentBookmark
    extra = 0
    readonly_fields = ("user", "created_at")
    can_delete = False


class RatingInline(admin.TabularInline):
    model = ContentRating
    extra = 0
    readonly_fields = ("user", "rating", "created_at", "updated_at")
    can_delete = False


# -----------------------------
# Category Admin
# -----------------------------

@admin.register(ContentCategory)
class ContentCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "is_active", "sort_order", "items_count")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    ordering = ("sort_order", "id")
    inlines = [ContentItemInline]

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = "Items"


# -----------------------------
# Content Item Admin
# -----------------------------

@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "thumbnail_preview",
        "title",
        "content_type",
        "category",
        "is_premium",
        "is_active",
        "metric_display",
        "rating_avg",
        "rating_count",
        "enrolled_count",
        "sort_order",
    )
    list_filter = ("content_type", "is_premium", "is_active", "category", "created_at")
    search_fields = ("title", "description", "external_url")
    ordering = ("sort_order", "-created_at", "id")

    readonly_fields = (
        "thumbnail_preview",
        "metric_display",
        "rating_avg",
        "rating_count",
        "enrolled_count",
        "created_at",
    )

    fieldsets = (
        ("Basic", {
            "fields": ("title", "description", "category", "content_type")
        }),
        ("Media", {
            "fields": ("thumbnail", "thumbnail_preview", "file", "external_url")
        }),
        ("Metrics", {
            "fields": ("duration_minutes", "read_minutes", "course_weeks", "metric_display")
        }),
        ("Flags & Ordering", {
            "fields": ("is_premium", "is_active", "sort_order", "created_at")
        }),
        ("Rating Summary", {
            "fields": ("rating_avg", "rating_count", "enrolled_count")
        }),
    )

    inlines = [EnrollmentInline, BookmarkInline, RatingInline]

    def thumbnail_preview(self, obj):
        if not obj.thumbnail:
            return "-"
        return format_html(
            '<img src="{}" style="height:40px;width:70px;object-fit:cover;border-radius:6px;" />',
            obj.thumbnail.url
        )
    thumbnail_preview.short_description = "Thumb"

    def metric_display(self, obj):
        # matches your UI: "45 min" / "12 min read" / "6 weeks"
        if obj.content_type in ("video", "audio"):
            return f"{obj.duration_minutes} min" if obj.duration_minutes else "-"
        if obj.content_type == "article":
            return f"{obj.read_minutes} min read" if obj.read_minutes else "-"
        if obj.content_type == "course":
            return f"{obj.course_weeks} weeks" if obj.course_weeks else "-"
        return "-"
    metric_display.short_description = "Metric"

    def enrolled_count(self, obj):
        return obj.enrollments.count()
    enrolled_count.short_description = "Enrolled"


# -----------------------------
# Optional: show raw tables too
# -----------------------------

@admin.register(ContentEnrollment)
class ContentEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("id", "item", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("item__title", "user__email")
    ordering = ("-created_at",)


@admin.register(ContentBookmark)
class ContentBookmarkAdmin(admin.ModelAdmin):
    list_display = ("id", "item", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("item__title", "user__email")
    ordering = ("-created_at",)


@admin.register(ContentRating)
class ContentRatingAdmin(admin.ModelAdmin):
    list_display = ("id", "item", "user", "rating", "created_at", "updated_at")
    list_filter = ("rating", "updated_at")
    search_fields = ("item__title", "user__email")
    ordering = ("-updated_at",)
