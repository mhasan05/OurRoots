from django.contrib import admin
from .models import *


class GroupMemberInline(admin.TabularInline):
    model = GroupMember
    extra = 0
    autocomplete_fields = ("user",)
    readonly_fields = ("joined_on",)


class PostCommentInline(admin.TabularInline):
    model = PostComment
    extra = 0
    readonly_fields = ("user", "created_on")


class PostReactionInline(admin.TabularInline):
    model = PostReaction
    extra = 0
    readonly_fields = ("user", "reaction_type", "created_on")



@admin.register(CommunityGroup)
class CommunityGroupAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "created_by",
        "is_private",
        "created_on",
    )

    list_filter = (
        "is_private",
        "created_on",
    )

    search_fields = (
        "name",
        "description",
    )

    ordering = ("-created_on",)

    readonly_fields = (
        "created_on",
        "updated_on",
    )

    inlines = [GroupMemberInline]



@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "group",
        "user",
        "role",
        "joined_on",
    )

    list_filter = (
        "role",
        "joined_on",
    )

    search_fields = (
        "user__email",
        "group__name",
    )

    ordering = ("-joined_on",)

    readonly_fields = ("joined_on",)



@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "author",
        "group",
        "is_pinned",
        "is_deleted",
        "created_on",
    )

    list_filter = (
        "is_pinned",
        "is_deleted",
        "created_on",
    )

    search_fields = (
        "content",
        "author__email",
    )

    ordering = ("-created_on",)

    readonly_fields = (
        "created_on",
        "updated_on",
    )

    inlines = [
        PostCommentInline,
        PostReactionInline,
    ]


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "post",
        "user",
        "created_on",
    )

    list_filter = (
        "created_on",
    )

    search_fields = (
        "comment",
        "user__email",
    )

    ordering = ("-created_on",)

    readonly_fields = ("created_on",)


@admin.register(PostReaction)
class PostReactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "post",
        "user",
        "reaction_type",
        "created_on",
    )

    list_filter = (
        "reaction_type",
        "created_on",
    )

    search_fields = (
        "user__email",
        "post__content",
    )

    ordering = ("-created_on",)

    readonly_fields = ("created_on",)
