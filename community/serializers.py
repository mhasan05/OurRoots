from rest_framework import serializers
from .models import *



class CommunityGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityGroup
        fields = "__all__"
        read_only_fields = ("created_by", "created_on")



class CommunityPostSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name", read_only=True)

    class Meta:
        model = CommunityPost
        fields = "__all__"
        read_only_fields = ("author", "created_on")



class PostCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = PostComment
        fields = "__all__"
        read_only_fields = ("user", "created_on")



class PostReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostReaction
        fields = "__all__"
        read_only_fields = ("user",)
