from django.urls import path
from . import views

urlpatterns = [
    path("plans/", views.SubscriptionPlanListAPIView.as_view()),
    path("me/", views.MySubscriptionAPIView.as_view()),
    path("subscribe/", views.SubscribeAPIView.as_view()),
    path("cancel/", views.CancelSubscriptionAPIView.as_view()),
    path("payments/", views.MyPaymentsAPIView.as_view()),

    # admin
    path("admin/plans/", views.AdminPlanListAPIView.as_view()),
    path("admin/plans/create/", views.AdminPlanCreateAPIView.as_view()),
    path("admin/plans/<int:plan_id>/", views.AdminPlanUpdateAPIView.as_view()),
    path("admin/plans/<int:plan_id>/delete/", views.AdminPlanDeleteAPIView.as_view()),
]