from rest_framework import serializers
from .models import *


class CulturalProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = CulturalProvider
        fields = "__all__"
        read_only_fields = ("user", "is_verified", "created_at")


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = "__all__"
        read_only_fields = ("provider", "created_at")


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = "__all__"
        read_only_fields = ("provider", "created_at")



class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = "__all__"
        read_only_fields = ("user", "status", "created_at")



class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = "__all__"
        read_only_fields = ("user", "created_at")


class CulturalProviderListSerializer(serializers.ModelSerializer):
    average_rating = serializers.DecimalField(
        source="providerstats.average_rating",
        max_digits=3,
        decimal_places=2,
        read_only=True,
    )

    total_reviews = serializers.IntegerField(
        source="providerstats.total_reviews",
        read_only=True,
    )

    class Meta:
        model = CulturalProvider
        fields = (
            "id",
            "name",
            "tagline",
            "country",
            "city",
            "is_verified",
            "average_rating",
            "total_reviews",
        )





class ProviderLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderLanguage
        fields = ("language",)


class ProviderSpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderSpecialty
        fields = ("specialty",)


class ExperienceMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = (
            "id",
            "title",
            "duration_hours",
            "location",
            "base_price",
        )


class CulturalProviderDetailSerializer(serializers.ModelSerializer):
    languages = ProviderLanguageSerializer(
        source="providerlanguage_set",
        many=True,
        read_only=True,
    )
    specialties = ProviderSpecialtySerializer(
        source="providerspecialty_set",
        many=True,
        read_only=True,
    )
    experiences = ExperienceMiniSerializer(
        source="experience_set",
        many=True,
        read_only=True,
    )

    stats = serializers.SerializerMethodField()

    class Meta:
        model = CulturalProvider
        fields = (
            "id",
            "name",
            "tagline",
            "bio",
            "country",
            "city",
            "contact_email",
            "contact_phone",
            "whatsapp_no",
            "website_url",
            "languages",
            "specialties",
            "experiences",
            "stats",
        )

    def get_stats(self, obj):
        if hasattr(obj, "providerstats"):
            return {
                "average_rating": obj.providerstats.average_rating,
                "total_reviews": obj.providerstats.total_reviews,
                "total_bookings": obj.providerstats.total_bookings,
            }
        return None
