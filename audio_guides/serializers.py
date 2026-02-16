from rest_framework import serializers
from .models import AudioCategory, AudioGuide, AudioGuideProgress


class AudioCategorySerializer(serializers.ModelSerializer):
    guides_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = AudioCategory
        fields = ["id", "name", "slug", "description", "sort_order", "guides_count"]


class AudioGuideListSerializer(serializers.ModelSerializer):
    category = AudioCategorySerializer(read_only=True)
    cover_image_url = serializers.SerializerMethodField()
    duration_mmss = serializers.CharField(read_only=True)

    class Meta:
        model = AudioGuide
        fields = [
            "id",
            "title",
            "subtitle",
            "description",
            "category",
            "duration_seconds",
            "duration_mmss",
            "cover_image_url",
            "is_featured",
        ]

    def get_cover_image_url(self, obj):
        if not obj.cover_image:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.cover_image.url) if request else obj.cover_image.url


class AudioGuideDetailSerializer(serializers.ModelSerializer):
    category = AudioCategorySerializer(read_only=True)
    cover_image_url = serializers.SerializerMethodField()
    audio_file_url = serializers.SerializerMethodField()
    duration_mmss = serializers.CharField(read_only=True)

    # show user progress if logged in
    user_progress = serializers.SerializerMethodField()

    class Meta:
        model = AudioGuide
        fields = [
            "id",
            "title",
            "subtitle",
            "description",
            "category",
            "duration_seconds",
            "duration_mmss",
            "cover_image_url",
            "audio_file_url",
            "audio_url",
            "is_featured",
            "user_progress",
        ]

    def get_cover_image_url(self, obj):
        if not obj.cover_image:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.cover_image.url) if request else obj.cover_image.url

    def get_audio_file_url(self, obj):
        if not obj.audio_file:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.audio_file.url) if request else obj.audio_file.url

    def get_user_progress(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            return None

        p = AudioGuideProgress.objects.filter(user=user, guide=obj).first()
        if not p:
            return {"position_seconds": 0, "is_completed": False}

        return {"position_seconds": p.position_seconds, "is_completed": p.is_completed}


class SaveProgressSerializer(serializers.Serializer):
    position_seconds = serializers.IntegerField(min_value=0)
    is_completed = serializers.BooleanField(required=False)
