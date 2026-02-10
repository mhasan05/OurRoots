from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL



class CommunityGroup(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="community/groups/", null=True, blank=True)

    is_private = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_groups")

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name




class GroupMember(models.Model):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("member", "Member"),
    )

    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(CommunityGroup, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")

    joined_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("group", "user")




class CommunityPost(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(
        CommunityGroup,
        on_delete=models.CASCADE,
        related_name="posts",
        null=True,
        blank=True,
    )

    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    image = models.ImageField(upload_to="community/posts/", null=True, blank=True)

    is_pinned = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)




class PostComment(models.Model):
    id = models.BigAutoField(primary_key=True)
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()

    created_on = models.DateTimeField(auto_now_add=True)




class PostReaction(models.Model):
    REACTION_CHOICES = (
        ("like", "Like"),
        ("support", "Support"),
        ("insightful", "Insightful"),
    )

    id = models.BigAutoField(primary_key=True)
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=20, choices=REACTION_CHOICES)

    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("post", "user")
