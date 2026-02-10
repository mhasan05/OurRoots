from rest_framework import serializers
from django.utils import timezone
from .models import (
    JourneyStage, GuidedExercise, EmotionTopic, StageResource, ReadinessChecklistItem,
    UserStageProgress, UserExerciseProgress, UserChecklistProgress
)


class JourneyStageListSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()

    class Meta:
        model = JourneyStage
        fields = [
            "id", "number", "title", "subtitle", "description",
            "bullet_1", "bullet_2", "bullet_3",
            "progress"
        ]

    def get_progress(self, stage):
        user = self.context["request"].user
        p = UserStageProgress.objects.filter(user=user, stage=stage).first()
        return {
            "percent_complete": p.percent_complete if p else 0,
            "is_completed": bool(p and p.completed_at),
        }


class GuidedExerciseSerializer(serializers.ModelSerializer):
    user_status = serializers.SerializerMethodField()

    class Meta:
        model = GuidedExercise
        fields = ["id", "title", "duration_minutes", "content", "sort_order", "user_status"]

    def get_user_status(self, obj):
        user = self.context["request"].user
        p = UserExerciseProgress.objects.filter(user=user, exercise=obj).first()
        return {"is_completed": bool(p and p.is_completed)}


class EmotionTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmotionTopic
        fields = ["id", "title", "description", "what_helps", "sort_order"]


class StageResourceSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = StageResource
        fields = [
            "id", "resource_type", "title", "description",
            "duration_minutes", "read_minutes", "url", "file_url", "sort_order"
        ]

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None


class ChecklistItemSerializer(serializers.ModelSerializer):
    user_status = serializers.SerializerMethodField()

    class Meta:
        model = ReadinessChecklistItem
        fields = ["id", "text", "hint", "sort_order", "user_status"]

    def get_user_status(self, obj):
        user = self.context["request"].user
        p = UserChecklistProgress.objects.filter(user=user, item=obj).first()
        return {"is_checked": bool(p and p.is_checked)}


class StageDetailSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()
    exercises = serializers.SerializerMethodField()
    emotions = EmotionTopicSerializer(many=True, read_only=True)
    resources = serializers.SerializerMethodField()
    checklist_items = serializers.SerializerMethodField()

    class Meta:
        model = JourneyStage
        fields = [
            "id", "number", "title", "subtitle", "description",
            "bullet_1", "bullet_2", "bullet_3",
            "progress",
            "exercises",
            "emotions",
            "resources",
            "checklist_items",
        ]

    def get_progress(self, stage):
        user = self.context["request"].user
        p = UserStageProgress.objects.filter(user=user, stage=stage).first()
        return {
            "percent_complete": p.percent_complete if p else 0,
            "is_completed": bool(p and p.completed_at),
        }

    def get_exercises(self, stage):
        qs = stage.exercises.all()
        return GuidedExerciseSerializer(qs, many=True, context=self.context).data

    def get_resources(self, stage):
        qs = stage.resources.all()
        return StageResourceSerializer(qs, many=True, context=self.context).data

    def get_checklist_items(self, stage):
        qs = stage.checklist_items.all()
        return ChecklistItemSerializer(qs, many=True, context=self.context).data


class UpdateStageProgressSerializer(serializers.Serializer):
    percent_complete = serializers.IntegerField(min_value=0, max_value=100)


class ToggleExerciseSerializer(serializers.Serializer):
    is_completed = serializers.BooleanField()


class ToggleChecklistSerializer(serializers.Serializer):
    is_checked = serializers.BooleanField()
