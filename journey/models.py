from django.conf import settings
from django.db import models
from django.utils import timezone


class JourneyStage(models.Model):
    number = models.PositiveIntegerField(unique=True)  # 1..6
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    # Optional: for cards in overview
    bullet_1 = models.CharField(max_length=255, blank=True)
    bullet_2 = models.CharField(max_length=255, blank=True)
    bullet_3 = models.CharField(max_length=255, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"{self.number}. {self.title}"


class GuidedExercise(models.Model):
    stage = models.ForeignKey(JourneyStage, on_delete=models.CASCADE, related_name="exercises")
    title = models.CharField(max_length=255)
    duration_minutes = models.PositiveIntegerField(default=10)
    content = models.TextField(blank=True)  # can be markdown/html/plain

    sort_order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.stage.number} - {self.title}"


class EmotionTopic(models.Model):
    stage = models.ForeignKey(JourneyStage, on_delete=models.CASCADE, related_name="emotions")
    title = models.CharField(max_length=255)  # e.g. "Will they accept me?"
    description = models.TextField(blank=True)
    what_helps = models.TextField(blank=True)

    sort_order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.stage.number} - {self.title}"


class StageResource(models.Model):
    TYPE_VIDEO = "video"
    TYPE_AUDIO = "audio"
    TYPE_ARTICLE = "article"
    TYPE_DOWNLOAD = "download"

    TYPE_CHOICES = [
        (TYPE_VIDEO, "Video"),
        (TYPE_AUDIO, "Audio"),
        (TYPE_ARTICLE, "Article"),
        (TYPE_DOWNLOAD, "Download"),
    ]

    stage = models.ForeignKey(JourneyStage, on_delete=models.CASCADE, related_name="resources")
    resource_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    duration_minutes = models.PositiveIntegerField(null=True, blank=True)  # for video/audio
    read_minutes = models.PositiveIntegerField(null=True, blank=True)      # for articles
    url = models.URLField(blank=True)                                      # external
    file = models.FileField(upload_to="journey/resources/", blank=True, null=True)  # PDFs, etc.

    sort_order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.stage.number} - {self.resource_type} - {self.title}"


class ReadinessChecklistItem(models.Model):
    stage = models.ForeignKey(JourneyStage, on_delete=models.CASCADE, related_name="checklist_items")
    text = models.CharField(max_length=255)
    hint = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.stage.number} - {self.text[:40]}"


# -------------------------
# User Progress
# -------------------------

class UserStageProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="journey_stage_progress")
    stage = models.ForeignKey(JourneyStage, on_delete=models.CASCADE, related_name="user_progress")

    percent_complete = models.PositiveIntegerField(default=0)  # 0..100
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "stage")

    def __str__(self):
        return f"{self.user_id} - Stage {self.stage.number} - {self.percent_complete}%"


class UserExerciseProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="journey_exercise_progress")
    exercise = models.ForeignKey(GuidedExercise, on_delete=models.CASCADE, related_name="user_progress")

    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "exercise")


class UserChecklistProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="journey_checklist_progress")
    item = models.ForeignKey(ReadinessChecklistItem, on_delete=models.CASCADE, related_name="user_progress")

    is_checked = models.BooleanField(default=False)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "item")
