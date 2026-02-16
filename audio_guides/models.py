from django.conf import settings
from django.db import models
from django.utils import timezone


class AudioCategory(models.Model):
    """
    Tabs/filters:
    - Pre-departure
    - In Ghana - Sacred Journey
    - In Ghana - Cultural Immersion
    - Post-Journey Reflection
    """
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)

    sort_order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name


class AudioGuide(models.Model):
    """
    Audio guide card + player content.
    """
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    category = models.ForeignKey(
        AudioCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="guides",
    )

    cover_image = models.ImageField(upload_to="audio_guides/covers/", null=True, blank=True)

    # audio source
    audio_file = models.FileField(upload_to="audio_guides/audio/", null=True, blank=True)
    audio_url = models.URLField(blank=True)  # optional external CDN stream

    duration_seconds = models.PositiveIntegerField(default=0)

    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["sort_order", "-created_at", "id"]

    def __str__(self):
        return self.title

    @property
    def duration_mmss(self):
        m = self.duration_seconds // 60
        s = self.duration_seconds % 60
        return f"{m:02d}:{s:02d}"


class AudioGuideDownload(models.Model):
    guide = models.ForeignKey(AudioGuide, on_delete=models.CASCADE, related_name="downloads")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    downloaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"download guide={self.guide_id} user={self.user_id}"


class AudioGuideProgress(models.Model):
    guide = models.ForeignKey(AudioGuide, on_delete=models.CASCADE, related_name="progress_entries")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="audio_progress")

    position_seconds = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("guide", "user")

    def __str__(self):
        return f"progress guide={self.guide_id} user={self.user_id} pos={self.position_seconds}"
