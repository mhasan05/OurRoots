from django.urls import path
from .views import *

urlpatterns = [
    path("signup/", SignupAPIView.as_view()),
    path("verify-email/", VerifyEmailAPIView.as_view()),
    path("resend-otp/", ResendOTPAPIView.as_view()),
    path("login/", LoginAPIView.as_view()),
    path("send-otp/", ForgotPasswordAPIView.as_view()),
    path("reset-password/", ResetPasswordAPIView.as_view()),

    path("profile/", UserProfileAPIView.as_view()),
    path("profile/update/", UpdateUserProfileAPIView.as_view()),
]
