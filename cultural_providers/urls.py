from django.urls import path
from .views import *

urlpatterns = [
    path("profile/", ProviderProfileAPIView.as_view()),
    path("providers/", ProviderListAPIView.as_view()),
    path("experience/create/", CreateExperienceAPIView.as_view()),
    path("booking/create/", CreateBookingAPIView.as_view()),
    path("review/create/", AddReviewAPIView.as_view()),

    path("providers/", AllProvidersAPIView.as_view()),
    path("providers/<int:provider_id>/", ProviderDetailAPIView.as_view()),
]
