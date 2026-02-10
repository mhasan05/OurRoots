from django.conf import settings
from django.db import models
from django.utils import timezone
import uuid


class Trip(models.Model):
    title = models.CharField(max_length=200)
    destination = models.CharField(max_length=200, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_trips",
    )

    share_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.title} ({self.destination})"


class TripMember(models.Model):
    ROLE_OWNER = "owner"
    ROLE_EDITOR = "editor"
    ROLE_VIEWER = "viewer"

    STATUS_INVITED = "invited"
    STATUS_ACCEPTED = "accepted"

    ROLE_CHOICES = [
        (ROLE_OWNER, "Owner"),
        (ROLE_EDITOR, "Editor"),
        (ROLE_VIEWER, "Viewer"),
    ]

    STATUS_CHOICES = [
        (STATUS_INVITED, "Invited"),
        (STATUS_ACCEPTED, "Accepted"),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trip_memberships")

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_VIEWER)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_INVITED)

    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_trip_invites",
    )

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("trip", "user")

    def __str__(self):
        return f"{self.user_id} in {self.trip_id} ({self.role}, {self.status})"


class TripDay(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="days")
    day_number = models.PositiveIntegerField()  # Day 1, Day 2...
    date = models.DateField(null=True, blank=True)
    title = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ("trip", "day_number")
        ordering = ["day_number"]

    def __str__(self):
        return f"{self.trip_id} Day {self.day_number}"


class TripActivity(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="activities")
    day = models.ForeignKey(TripDay, on_delete=models.CASCADE, related_name="activities")

    title = models.CharField(max_length=255)
    location_name = models.CharField(max_length=255, blank=True)

    start_time = models.TimeField(null=True, blank=True)  # 09:00 AM
    sort_order = models.PositiveIntegerField(default=1)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_trip_activities",
    )

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["day__day_number", "sort_order", "start_time", "id"]

    def __str__(self):
        return f"{self.title} (Trip {self.trip_id}, Day {self.day.day_number})"


class ActivityMessage(models.Model):
    activity = models.ForeignKey(TripActivity, on_delete=models.CASCADE, related_name="messages")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activity_messages")
    message = models.TextField()

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"Msg {self.id} on activity {self.activity_id}"


class ActivityReaction(models.Model):
    activity = models.ForeignKey(TripActivity, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activity_reactions")

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("activity", "user")

    def __str__(self):
        return f"Like {self.user_id} -> {self.activity_id}"
