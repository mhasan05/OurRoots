from django.contrib import admin
from .models import Quiz, Question, Option, UserAnswer


class OptionInline(admin.TabularInline):
    model = Option
    extra = 0
    ordering = ("order_index",)


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    ordering = ("order_index",)
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "created_by",
        "is_published",
        "created_on",
    )

    list_filter = (
        "is_published",
        "created_on",
    )

    search_fields = (
        "title",
        "description",
    )

    ordering = ("-created_on",)

    inlines = [QuestionInline]

    readonly_fields = (
        "created_on",
        "updated_on",
    )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "quiz",
        "question_type",
        "order_index",
        "points",
    )

    list_filter = (
        "question_type",
        "quiz",
    )

    search_fields = (
        "question_text",
    )

    ordering = ("quiz", "order_index")

    inlines = [OptionInline]

    readonly_fields = (
        "created_on",
        "updated_on",
    )


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "question",
        "option_text",
        "is_correct",
        "order_index",
    )

    list_filter = (
        "is_correct",
    )

    ordering = ("question", "order_index")

    search_fields = (
        "option_text",
    )

    readonly_fields = (
        "created_on",
        "updated_on",
    )


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "question",
        "option",
        "created_on",
    )

    list_filter = (
        "created_on",
    )

    search_fields = (
        "user__email",
        "question__question_text",
    )

    ordering = ("-created_on",)

    readonly_fields = (
        "created_on",
        "updated_on",
    )
