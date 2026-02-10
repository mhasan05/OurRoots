from django.urls import path
from . import views

urlpatterns = [
    # Meta: styles, experiences, resources
    path("meta/", views.BudgetMetaAPIView.as_view()),

    # session management
    path("session/", views.BudgetSessionAPIView.as_view()),

    # wizard steps
    path("set-style/", views.SetStyleAPIView.as_view()),
    path("set-duration/", views.SetDurationAPIView.as_view()),
    path("set-experiences/", views.SetExperiencesAPIView.as_view()),
    path("generate-breakdown/", views.GenerateCostBreakdownAPIView.as_view()),
    path("update-breakdown/", views.UpdateBreakdownAPIView.as_view()),
    path("finalize/", views.FinalizeBudgetAPIView.as_view()),

    # sharing
    path("share/", views.ShareWithProviderAPIView.as_view()),
]
