from django.contrib import admin
from .models import (
    JourneyStage, GuidedExercise, EmotionTopic, StageResource, ReadinessChecklistItem,
    UserStageProgress, UserExerciseProgress, UserChecklistProgress
)

admin.site.register(JourneyStage)
admin.site.register(GuidedExercise)
admin.site.register(EmotionTopic)
admin.site.register(StageResource)
admin.site.register(ReadinessChecklistItem)

admin.site.register(UserStageProgress)
admin.site.register(UserExerciseProgress)
admin.site.register(UserChecklistProgress)
