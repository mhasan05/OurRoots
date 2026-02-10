from django.urls import path
from .views import *

urlpatterns = [
    # Community Groups
    path("groups/create/", CreateCommunityGroupAPIView.as_view(), name="community-group-create"),
    path("groups/", ListCommunityGroupsAPIView.as_view(), name="community-group-list"),

    # Posts
    path("posts/create/", CreatePostAPIView.as_view(), name="community-post-create"),
    path("posts/", ListPostsAPIView.as_view(), name="community-post-list"),

    # Comments
    path("comments/create/", AddCommentAPIView.as_view(), name="community-comment-create"),

    # Reactions
    path("reactions/", ReactPostAPIView.as_view(), name="community-post-react"),
]
