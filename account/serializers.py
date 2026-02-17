from rest_framework import serializers
from .models import User
from django.contrib.auth.hashers import make_password

class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "full_name", "email", "password")

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])
        return super().create(validated_data)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()
    new_password = serializers.CharField()

class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()

class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "full_name",
            "email",
            "phone",
            "image",
            "role",
            "user_type",
            "heritage_connection",
            "source",
            "created_on",
        )
        read_only_fields = (
            "id",
            "email",
            "role",
            "user_type",
            "created_on",
        )


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "full_name",
            "phone",
            "image",
            "heritage_connection",
            "source",
        )
