from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import *
from .serializers import *


class CreateCommunityGroupAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CommunityGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.save(created_by=request.user)

        GroupMember.objects.create(
            group=group,
            user=request.user,
            role="admin",
        )

        return Response(serializer.data, status=201)
    


class ListCommunityGroupsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        groups = CommunityGroup.objects.all()
        return Response(CommunityGroupSerializer(groups, many=True).data)



class CreatePostAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CommunityPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user)
        return Response(serializer.data, status=201)



class ListPostsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        group_id = request.query_params.get("group_id")
        posts = CommunityPost.objects.filter(is_deleted=False)

        if group_id:
            posts = posts.filter(group_id=group_id)

        return Response(CommunityPostSerializer(posts, many=True).data)



class AddCommentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PostCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=201)



class ReactPostAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PostReactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reaction, created = PostReaction.objects.update_or_create(
            post=serializer.validated_data["post"],
            user=request.user,
            defaults={"reaction_type": serializer.validated_data["reaction_type"]},
        )

        return Response({"message": "Reaction saved"})
