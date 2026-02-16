from django.urls import path
from . import views

urlpatterns = [
    # Public
    path("categories/", views.AudioCategoryListAPIView.as_view()),
    path("guides/", views.AudioGuideListAPIView.as_view()),
    path("guides/<int:guide_id>/", views.AudioGuideDetailAPIView.as_view()),

    # Auth
    path("guides/<int:guide_id>/progress/", views.AudioGuideSaveProgressAPIView.as_view()),
    path("guides/<int:guide_id>/download/", views.AudioGuideDownloadAPIView.as_view()),

    # Staff/Admin - categories
    path("admin/categories/create/", views.AdminAudioCategoryCreateAPIView.as_view()),
    path("admin/categories/<int:category_id>/update/", views.AdminAudioCategoryUpdateAPIView.as_view()),
    path("admin/categories/<int:category_id>/delete/", views.AdminAudioCategoryDeleteAPIView.as_view()),

    # Staff/Admin - guides
    path("admin/guides/create/", views.AdminAudioGuideCreateAPIView.as_view()),
    path("admin/guides/<int:guide_id>/update/", views.AdminAudioGuideUpdateAPIView.as_view()),
    path("admin/guides/<int:guide_id>/delete/", views.AdminAudioGuideDeleteAPIView.as_view()),
]
