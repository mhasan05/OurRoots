from django.db import models
from django.contrib.auth.models import AbstractBaseUser,PermissionsMixin
from django.utils import timezone
from account.manager import UserManager #import from account apps



class User(AbstractBaseUser,PermissionsMixin):
    class Meta:
        verbose_name_plural = "User"
    ROLE_CHOICES = (
        ("user", "User"),
        ("admin", "Admin"),
        ("provider", "Service Provider"),
    )

    id = models.BigAutoField(primary_key=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    image = models.ImageField(upload_to="users/", null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")

    heritage_connection = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=100, blank=True, null=True)

    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_expired_on = models.DateTimeField(blank=True, null=True)

    google_id = models.CharField(max_length=255, blank=True, null=True)
    facebook_id = models.CharField(max_length=255, blank=True, null=True)
    apple_id = models.CharField(max_length=255, blank=True, null=True)

    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    def __str__(self):
        return self.email
