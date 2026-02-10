from django.urls import path
from . import views

urlpatterns = [
    path("trips/", views.TripListAPIView.as_view()),
    path("trips/create/", views.TripCreateAPIView.as_view()),
    path("trips/<int:trip_id>/", views.TripDetailAPIView.as_view()),

    path("trips/<int:trip_id>/invite/", views.TripInviteAPIView.as_view()),
    path("trips/<int:trip_id>/accept-invite/", views.TripAcceptInviteAPIView.as_view()),
    path("trips/join-by-token/", views.TripJoinByTokenAPIView.as_view()),

    path("trips/<int:trip_id>/days/add/", views.TripDayAddAPIView.as_view()),
    path("trips/<int:trip_id>/activities/add/", views.TripActivityAddAPIView.as_view()),

    path("activities/<int:activity_id>/update/", views.TripActivityUpdateAPIView.as_view()),
    path("activities/<int:activity_id>/delete/", views.TripActivityDeleteAPIView.as_view()),

    path("activities/<int:activity_id>/messages/", views.ActivityMessagesAPIView.as_view()),
    path("activities/<int:activity_id>/messages/add/", views.ActivityMessageAddAPIView.as_view()),

    path("activities/<int:activity_id>/like/", views.ActivityLikeToggleAPIView.as_view()),
]
