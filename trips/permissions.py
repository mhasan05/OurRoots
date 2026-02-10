from rest_framework.permissions import BasePermission
from .models import TripMember


def get_membership(user, trip):
    if not user or not user.is_authenticated:
        return None
    return TripMember.objects.filter(trip=trip, user=user, status=TripMember.STATUS_ACCEPTED).first()


class IsTripMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        trip = getattr(obj, "trip", None) or obj  # supports Trip or related objects
        return get_membership(request.user, trip) is not None


class CanEditTrip(BasePermission):
    """
    Owner/editor can create/update/delete days/activities/messages.
    Viewer is read-only (except accepting invites / joining).
    """

    def has_object_permission(self, request, view, obj):
        trip = getattr(obj, "trip", None) or obj
        membership = get_membership(request.user, trip)
        if not membership:
            return False
        return membership.role in (TripMember.ROLE_OWNER, TripMember.ROLE_EDITOR)
