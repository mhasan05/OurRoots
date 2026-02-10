from django.contrib import admin
from .models import Trip, TripMember, TripDay, TripActivity, ActivityMessage, ActivityReaction

admin.site.register(Trip)
admin.site.register(TripMember)
admin.site.register(TripDay)
admin.site.register(TripActivity)
admin.site.register(ActivityMessage)
admin.site.register(ActivityReaction)
