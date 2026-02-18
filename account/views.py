import random
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from django.contrib.auth import authenticate
from .models import User
from function.utils import generate_and_send_otp
from .serializers import *
from rest_framework.permissions import IsAuthenticated


def get_tokens_for_user(user):
    # refresh = RefreshToken.for_user(user)
    refresh = CustomTokenObtainPairSerializer.get_token(user)
    return str(refresh.access_token)

class SignupAPIView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        generate_and_send_otp(user)
        return Response({"message": "OTP sent to email"}, status=201)

class VerifyEmailAPIView(APIView):
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(
            email=serializer.validated_data["email"],
            otp=serializer.validated_data["otp"]
        ).first()

        if not user:
            return Response({"error": "Invalid OTP"}, status=400)

        user.is_active = True
        user.otp = None
        user.save()

        return Response({"message": "Email verified"})

class ResendOTPAPIView(APIView):
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.get(email=serializer.validated_data["email"])
        generate_and_send_otp(user)

        return Response({"message": "OTP resent"})

class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"]
        )

        if not user:
            return Response({"error": "Invalid credentials"}, status=401)
        tokens = get_tokens_for_user(user)

        return Response({
            "status":"success",
            "message": "Login successful.",
            "access_token": tokens,
            "data": serializer.data
        }, status=200)

class ForgotPasswordAPIView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.get(email=serializer.validated_data["email"])
        generate_and_send_otp(user)

        return Response({"message": "OTP sent for reset"})

class ResetPasswordAPIView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(
            email=serializer.validated_data["email"],
            otp=serializer.validated_data["otp"]
        ).first()

        if not user:
            return Response({"error": "Invalid OTP"}, status=400)

        user.set_password(serializer.validated_data["new_password"])
        user.otp = None
        user.save()

        return Response({"message": "Password reset successful"})
    



class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class UpdateUserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "message": "Profile updated successfully",
                "data": UserDetailSerializer(request.user).data,
            },
            status=status.HTTP_200_OK,
        )


