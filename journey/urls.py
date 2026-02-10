from django.urls import path
from . import views

urlpatterns = [
    # Overview page (6 cards + progress bar)
    path("stages/", views.JourneyOverviewAPIView.as_view()),

    # Stage detail page
    path("stages/<int:stage_number>/", views.StageDetailAPIView.as_view()),

    # Update overall stage progress (if you want manual progress bar)
    path("stages/<int:stage_number>/progress/", views.UpdateStageProgressAPIView.as_view()),

    # Toggle completion
    path("exercises/<int:exercise_id>/toggle/", views.ToggleExerciseCompletionAPIView.as_view()),
    path("checklist/<int:item_id>/toggle/", views.ToggleChecklistItemAPIView.as_view()),
]
