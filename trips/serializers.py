from rest_framework import serializers
from django.db import transaction
from .models import (
    Trip, TripMember, TripDay, TripActivity, ActivityMessage, ActivityReaction
)


class SimpleUserSerializer(serializers.Serializer):
    # Keeps you independent of your account serializers
    id = serializers.IntegerField()
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)


class TripMemberSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = TripMember
        fields = ["id", "user", "role", "status", "created_at"]

    def get_user(self, obj):
        u = obj.user
        return {
            "id": u.id,
            "email": getattr(u, "email", ""),
            "first_name": getattr(u, "first_name", ""),
            "last_name": getattr(u, "last_name", ""),
        }


class TripCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = ["id", "title", "destination", "start_date", "end_date"]

    def create(self, validated_data):
        user = self.context["request"].user
        with transaction.atomic():
            trip = Trip.objects.create(created_by=user, **validated_data)
            TripMember.objects.create(
                trip=trip,
                user=user,
                role=TripMember.ROLE_OWNER,
                status=TripMember.STATUS_ACCEPTED,
                invited_by=user,
            )
        return trip


class TripDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = TripDay
        fields = ["id", "day_number", "date", "title"]


class TripActivitySerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = TripActivity
        fields = [
            "id", "trip", "day", "title", "location_name",
            "start_time", "sort_order", "created_by",
            "likes_count", "comments_count", "created_at",
        ]
        read_only_fields = ["trip", "created_by", "created_at"]

    def get_created_by(self, obj):
        u = obj.created_by
        if not u:
            return None
        return {"id": u.id, "email": getattr(u, "email", "")}


class ActivityMessageSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = ActivityMessage
        fields = ["id", "activity", "user", "message", "created_at"]
        read_only_fields = ["activity", "user", "created_at"]

    def get_user(self, obj):
        u = obj.user
        return {"id": u.id, "email": getattr(u, "email", "")}


class TripDetailSerializer(serializers.ModelSerializer):
    members = TripMemberSerializer(many=True, read_only=True)
    days = TripDaySerializer(many=True, read_only=True)
    activities = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            "id", "title", "destination", "start_date", "end_date",
            "created_by", "share_token", "created_at",
            "members", "days", "activities",
        ]

    def get_activities(self, trip):
        # annotate counts without extra endpoints
        qs = TripActivity.objects.filter(trip=trip).select_related("day", "created_by")
        # manual counts (simple, reliable)
        data = []
        for a in qs:
            data.append({
                "id": a.id,
                "day": a.day_id,
                "day_number": a.day.day_number,
                "title": a.title,
                "location_name": a.location_name,
                "start_time": a.start_time,
                "sort_order": a.sort_order,
                "created_by": {"id": a.created_by_id} if a.created_by_id else None,
                "likes_count": a.reactions.count(),
                "comments_count": a.messages.count(),
                "created_at": a.created_at,
            })
        return data
