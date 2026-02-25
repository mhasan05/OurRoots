from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class SubscriptionPlan(models.Model):
    """
    Plans shown in UI: Free / Community / Preparation / Premium
    """
    TIER_CHOICES = (
        ("free", "Free"),
        ("community", "Community"),
        ("preparation", "Preparation"),
        ("premium", "Premium"),
    )

    id = models.BigAutoField(primary_key=True)
    tier = models.CharField(max_length=30, choices=TIER_CHOICES, unique=True)

    name = models.CharField(max_length=80)                 # "Preparation"
    description = models.TextField(blank=True)             # subtitle in UI

    # pricing (base USD per month)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # UI flags
    is_active = models.BooleanField(default=True)
    is_most_popular = models.BooleanField(default=False)

    # entitlements flags (use these in your app)
    can_access_premium_content = models.BooleanField(default=False)
    can_plan_trip_together = models.BooleanField(default=False)
    can_use_budget_guide = models.BooleanField(default=False)
    can_access_audio_guides = models.BooleanField(default=False)

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["price_usd", "id"]

    def __str__(self):
        return f"{self.name} ({self.tier})"


class UserSubscription(models.Model):
    """
    The currently active subscription for a user.
    """
    STATUS = (
        ("active", "Active"),
        ("past_due", "Past Due"),
        ("canceled", "Canceled"),
        ("expired", "Expired"),
    )

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="user_subscriptions")

    status = models.CharField(max_length=20, choices=STATUS, default="active")

    # billing
    started_at = models.DateTimeField(default=timezone.now)
    current_period_start = models.DateTimeField(default=timezone.now)
    current_period_end = models.DateTimeField(null=True, blank=True)

    # store stripe references later
    provider = models.CharField(max_length=30, default="manual")  # manual/stripe/paypal
    provider_customer_id = models.CharField(max_length=120, blank=True)
    provider_subscription_id = models.CharField(max_length=120, blank=True)

    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["current_period_end"]),
        ]

    def __str__(self):
        return f"{self.user_id} -> {self.plan.tier} ({self.status})"

    @property
    def is_active(self):
        if self.status != "active":
            return False
        if self.current_period_end and timezone.now() > self.current_period_end:
            return False
        return True


class SubscriptionPayment(models.Model):
    """
    Records payments (for receipts, audit, and later Stripe webhooks).
    """
    STATUS = (
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    )

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name="payments")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")
    status = models.CharField(max_length=20, choices=STATUS, default="pending")

    provider = models.CharField(max_length=30, default="manual")  # stripe/manual
    provider_payment_id = models.CharField(max_length=120, blank=True)

    paid_at = models.DateTimeField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_on"]