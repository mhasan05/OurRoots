from django.conf import settings
from django.db import models
from django.utils import timezone


class BudgetResource(models.Model):
    """Right-side card: Budget Resources (articles/videos)"""
    title = models.CharField(max_length=255)
    read_minutes = models.PositiveIntegerField(default=5)
    url = models.URLField(blank=True)

    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class BudgetStyle(models.Model):
    """Step-1 cards"""
    key = models.CharField(max_length=50, unique=True)  # budget, cultural, premium, ancestral
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class BudgetExperience(models.Model):
    """Step-3 experiences (user selects 3 experiences etc.)"""
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # default per-experience cost range
    min_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class BudgetCategoryRule(models.Model):
    """
    Step-4 categories + default price ranges.
    You can tune by budget style if needed.
    """
    CAT_FLIGHTS = "flights"
    CAT_ACCOM = "accommodation"
    CAT_TRANSPORT = "transportation"
    CAT_FOOD = "food"
    CAT_EXPERIENCES = "experiences"
    CAT_EMERGENCY = "emergency"

    CATEGORY_CHOICES = [
        (CAT_FLIGHTS, "Flights"),
        (CAT_ACCOM, "Accommodation"),
        (CAT_TRANSPORT, "Transportation"),
        (CAT_FOOD, "Food"),
        (CAT_EXPERIENCES, "Experiences"),
        (CAT_EMERGENCY, "Emergency Buffer"),
    ]

    style = models.ForeignKey(BudgetStyle, on_delete=models.CASCADE, related_name="category_rules")
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)

    # range guidance (shown under the category)
    min_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # default suggested value (pre-filled editable)
    default_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ("style", "category")

    def __str__(self):
        return f"{self.style.key} - {self.category}"


class BudgetSession(models.Model):
    """
    One saved budget plan per user (or multiple if you allow).
    """
    STEP_STYLE = 1
    STEP_DURATION = 2
    STEP_EXPERIENCES = 3
    STEP_BREAKDOWN = 4
    STEP_FINAL = 5

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budget_sessions")

    # step 1
    style = models.ForeignKey(BudgetStyle, on_delete=models.SET_NULL, null=True, blank=True)

    # step 2
    days = models.PositiveIntegerField(default=7)

    # step progress
    current_step = models.PositiveSmallIntegerField(default=1)

    # final totals
    total_estimate = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"BudgetSession {self.id} user={self.user_id}"


class BudgetSessionExperience(models.Model):
    session = models.ForeignKey(BudgetSession, on_delete=models.CASCADE, related_name="session_experiences")
    experience = models.ForeignKey(BudgetExperience, on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("session", "experience")


class BudgetSessionBreakdown(models.Model):
    session = models.OneToOneField(BudgetSession, on_delete=models.CASCADE, related_name="breakdown")

    flights = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    accommodation = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transportation = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    food = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    experiences = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    emergency = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def total(self):
        return (
            self.flights + self.accommodation + self.transportation +
            self.food + self.experiences + self.emergency
        )


class BudgetShare(models.Model):
    """Share with Provider (store share record; provider notifications can be added later)"""
    session = models.ForeignKey(BudgetSession, on_delete=models.CASCADE, related_name="shares")
    shared_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shared_budgets")

    provider_user_id = models.IntegerField(null=True, blank=True)  # if your providers are users
    note = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
