from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class CulturalProvider(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    name = models.CharField(max_length=255)
    tagline = models.CharField(max_length=255, blank=True)
    bio = models.TextField()

    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)

    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=30, blank=True)
    whatsapp_no = models.CharField(max_length=30, blank=True)
    website_url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)





class ProviderLanguage(models.Model):
    id = models.BigAutoField(primary_key=True)
    provider = models.ForeignKey(CulturalProvider, on_delete=models.CASCADE)
    language = models.CharField(max_length=100)



class ProviderSpecialty(models.Model):
    id = models.BigAutoField(primary_key=True)
    provider = models.ForeignKey(CulturalProvider, on_delete=models.CASCADE)
    specialty = models.CharField(max_length=255)




class Experience(models.Model):
    id = models.BigAutoField(primary_key=True)
    provider = models.ForeignKey(CulturalProvider, on_delete=models.CASCADE)

    title = models.CharField(max_length=255)
    description = models.TextField()
    duration_hours = models.PositiveIntegerField()

    location = models.CharField(max_length=255)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)




class ExperiencePackage(models.Model):
    id = models.BigAutoField(primary_key=True)
    experience = models.ForeignKey(Experience, on_delete=models.CASCADE)

    package_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    max_people = models.PositiveIntegerField()
    includes = models.TextField()




class Booking(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.ForeignKey(CulturalProvider, on_delete=models.CASCADE)
    experience = models.ForeignKey(Experience, on_delete=models.CASCADE)

    booking_date = models.DateField()
    number_of_people = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)



class Payment(models.Model):
    id = models.BigAutoField(primary_key=True)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")
    provider = models.CharField(max_length=50)  # Stripe / PayPal later
    status = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)



class Review(models.Model):
    id = models.BigAutoField(primary_key=True)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    provider = models.ForeignKey(CulturalProvider, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)



class ProviderStats(models.Model):
    provider = models.OneToOneField(CulturalProvider, on_delete=models.CASCADE)

    total_bookings = models.PositiveIntegerField(default=0)
    completed_bookings = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_reviews = models.PositiveIntegerField(default=0)

    last_updated = models.DateTimeField(auto_now=True)
