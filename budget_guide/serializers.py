from rest_framework import serializers
from .models import (
    BudgetStyle, BudgetExperience, BudgetCategoryRule,
    BudgetSession, BudgetSessionExperience, BudgetSessionBreakdown,
    BudgetResource, BudgetShare
)


class BudgetResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetResource
        fields = ["id", "title", "read_minutes", "url"]


class BudgetStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetStyle
        fields = ["id", "key", "title", "description"]


class BudgetExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetExperience
        fields = ["id", "title", "description", "min_cost", "max_cost"]


class CategoryRuleSerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = BudgetCategoryRule
        fields = ["category", "category_label", "min_cost", "max_cost", "default_cost"]


class BudgetSessionExperienceSerializer(serializers.ModelSerializer):
    experience = BudgetExperienceSerializer(read_only=True)
    experience_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = BudgetSessionExperience
        fields = ["id", "experience", "experience_id", "quantity"]


class BudgetBreakdownSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()

    class Meta:
        model = BudgetSessionBreakdown
        fields = ["flights", "accommodation", "transportation", "food", "experiences", "emergency", "total"]

    def get_total(self, obj):
        return obj.total()


class BudgetSessionSerializer(serializers.ModelSerializer):
    style = BudgetStyleSerializer(read_only=True)
    style_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    breakdown = BudgetBreakdownSerializer(read_only=True)
    session_experiences = BudgetSessionExperienceSerializer(many=True, read_only=True)

    class Meta:
        model = BudgetSession
        fields = [
            "id", "current_step", "style", "style_id",
            "days", "total_estimate",
            "session_experiences", "breakdown",
            "created_at", "updated_at",
        ]


class SetStyleSerializer(serializers.Serializer):
    style_key = serializers.CharField()


class SetDurationSerializer(serializers.Serializer):
    days = serializers.IntegerField(min_value=1, max_value=120)


class SetExperiencesSerializer(serializers.Serializer):
    experiences = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=True
    )
    # expected dict: { "experience_id": 1, "quantity": 2 }


class UpdateBreakdownSerializer(serializers.Serializer):
    flights = serializers.DecimalField(max_digits=12, decimal_places=2)
    accommodation = serializers.DecimalField(max_digits=12, decimal_places=2)
    transportation = serializers.DecimalField(max_digits=12, decimal_places=2)
    food = serializers.DecimalField(max_digits=12, decimal_places=2)
    experiences = serializers.DecimalField(max_digits=12, decimal_places=2)
    emergency = serializers.DecimalField(max_digits=12, decimal_places=2)


class ShareWithProviderSerializer(serializers.Serializer):
    provider_user_id = serializers.IntegerField(required=False, allow_null=True)
    note = serializers.CharField(required=False, allow_blank=True)
