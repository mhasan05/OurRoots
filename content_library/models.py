import math
from django.conf import settings
from django.db import models
from django.utils import timezone
from mutagen import File as MutagenFile


class ContentCategory(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)

    sort_order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name


class ContentItem(models.Model):
    TYPE_CHOICES = [
        ("video", "Video"),
        ("article", "Article"),
        ("audio", "Audio"),
        ("course", "Course"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    body_text = models.TextField(blank=True)

    category = models.ForeignKey(
        ContentCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
    )

    content_type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    thumbnail = models.ImageField(upload_to="content_library/thumbnails/", null=True, blank=True)
    file = models.FileField(upload_to="content_library/files/", null=True, blank=True)
    external_url = models.URLField(blank=True)

    duration_minutes = models.PositiveIntegerField(default=0)
    read_minutes = models.PositiveIntegerField(default=0)
    course_weeks = models.PositiveIntegerField(default=0)

    is_premium = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=1)

    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    rating_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["sort_order", "-created_at", "id"]

    def __str__(self):
        return self.title

    # -----------------------------
    # Auto Metric Calculations
    # -----------------------------

    def _calc_audio_duration_minutes(self):
        if not self.file:
            return 0
        try:
            f = self.file.file
            f.seek(0)
            audio = MutagenFile(f)
            if audio and hasattr(audio, "info") and getattr(audio.info, "length", None):
                seconds = float(audio.info.length)
                return int(max(1, round(seconds / 60)))
        except Exception:
            return 0
        return 0

    def _calc_read_minutes(self):
        text = (self.body_text or self.description or "").strip()
        if not text:
            return 0
        words = len(text.split())
        return int(max(1, math.ceil(words / 200)))  # 200 WPM

    def save(self, *args, **kwargs):
        if self.content_type in ("audio", "video"):
            if self.duration_minutes == 0 and self.file:
                self.duration_minutes = self._calc_audio_duration_minutes()

        if self.content_type == "article":
            if self.read_minutes == 0:
                self.read_minutes = self._calc_read_minutes()

        super().save(*args, **kwargs)


class ContentEnrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    item = models.ForeignKey(ContentItem, on_delete=models.CASCADE, related_name="enrollments")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "item")


class ContentBookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    item = models.ForeignKey(ContentItem, on_delete=models.CASCADE, related_name="bookmarks")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "item")


class ContentRating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    item = models.ForeignKey(ContentItem, on_delete=models.CASCADE, related_name="ratings")
    rating = models.PositiveSmallIntegerField(default=5)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "item")
