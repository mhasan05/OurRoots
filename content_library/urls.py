from django.urls import path
from . import views

urlpatterns = [
    # Public
    path("tabs/", views.ContentTabsAPIView.as_view()),
    path("items/", views.ContentListAPIView.as_view()),
    path("items/<int:item_id>/", views.ContentDetailAPIView.as_view()),

    # Auth actions
    path("items/<int:item_id>/enroll/", views.EnrollAPIView.as_view()),
    path("items/<int:item_id>/bookmark/", views.BookmarkToggleAPIView.as_view()),
    path("items/<int:item_id>/rate/", views.RateAPIView.as_view()),
    path("items/<int:item_id>/file/", views.ContentSecureFileAPIView.as_view()),


    # Staff/Admin categories
    path("admin/categories/create/", views.AdminCategoryCreateAPIView.as_view()),
    path("admin/categories/<int:category_id>/update/", views.AdminCategoryUpdateAPIView.as_view()),
    path("admin/categories/<int:category_id>/delete/", views.AdminCategoryDeleteAPIView.as_view()),

    # Staff/Admin content items
    path("admin/items/create/", views.AdminItemCreateAPIView.as_view()),
    path("admin/items/<int:item_id>/update/", views.AdminItemUpdateAPIView.as_view()),
    path("admin/items/<int:item_id>/delete/", views.AdminItemDeleteAPIView.as_view()),
]
