from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/quizzes/', include('quizzes.urls')),
    path('api/auth/', include('account.urls')),
    path('api/community/', include('community.urls')),
    path("api/providers/", include("cultural_providers.urls")),
    path("api/settings/", include("settings.urls")),
    path("api/trips/", include("trips.urls")),
    path("api/journey/", include("journey.urls")),
    path("api/budget/", include("budget_guide.urls")),
    path("api/audio/", include("audio_guides.urls")),
    path("api/content/", include("content_library.urls")),
    path("api/subscriptions/", include("subscription.urls")),
]
