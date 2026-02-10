from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Trip, TripMember, TripDay, TripActivity, ActivityMessage, ActivityReaction
from .serializers import (
    TripCreateSerializer, TripDetailSerializer,
    TripDaySerializer, TripActivitySerializer,
    ActivityMessageSerializer, TripMemberSerializer,
)
from .permissions import get_membership, CanEditTrip


class TripListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        trips = Trip.objects.filter(
            members__user=request.user,
            members__status=TripMember.STATUS_ACCEPTED
        ).distinct().order_by("-created_at")
        data = [{"id": t.id, "title": t.title, "destination": t.destination, "share_token": str(t.share_token)} for t in trips]
        return Response(data)

class TripCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TripCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        trip = serializer.save()
        return Response(TripDetailSerializer(trip).data, status=status.HTTP_201_CREATED)


class TripDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_id: int):
        trip = get_object_or_404(Trip, id=trip_id)
        if not get_membership(request.user, trip):
            return Response({"detail": "Not a trip member."}, status=403)
        return Response(TripDetailSerializer(trip).data)


class TripInviteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_id: int):
        trip = get_object_or_404(Trip, id=trip_id)
        membership = get_membership(request.user, trip)
        if not membership or membership.role not in (TripMember.ROLE_OWNER, TripMember.ROLE_EDITOR):
            return Response({"detail": "You don't have permission to invite."}, status=403)

        user_ids = request.data.get("user_ids", [])
        if not isinstance(user_ids, list) or not user_ids:
            return Response({"detail": "user_ids must be a non-empty list."}, status=400)

        # Try to use your AUTH_USER_MODEL
        User = request.user.__class__

        created = []
        with transaction.atomic():
            for uid in set(user_ids):
                if uid == request.user.id:
                    continue
                u = User.objects.filter(id=uid).first()
                if not u:
                    continue
                tm, _ = TripMember.objects.get_or_create(
                    trip=trip, user=u,
                    defaults={
                        "role": TripMember.ROLE_EDITOR,  # default: editor
                        "status": TripMember.STATUS_INVITED,
                        "invited_by": request.user,
                    }
                )
                if tm.status != TripMember.STATUS_ACCEPTED:
                    created.append(tm)

        return Response({
            "share_token": str(trip.share_token),
            "invites": TripMemberSerializer(created, many=True).data
        })


class TripAcceptInviteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_id: int):
        trip = get_object_or_404(Trip, id=trip_id)
        tm = TripMember.objects.filter(trip=trip, user=request.user).first()
        if not tm:
            return Response({"detail": "You are not invited to this trip."}, status=404)

        tm.status = TripMember.STATUS_ACCEPTED
        tm.save(update_fields=["status"])
        return Response({"detail": "Invite accepted."})


class TripJoinByTokenAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get("share_token")
        if not token:
            return Response({"detail": "share_token is required."}, status=400)

        trip = Trip.objects.filter(share_token=token).first()
        if not trip:
            return Response({"detail": "Invalid token."}, status=404)

        tm, _ = TripMember.objects.get_or_create(
            trip=trip,
            user=request.user,
            defaults={
                "role": TripMember.ROLE_VIEWER,
                "status": TripMember.STATUS_ACCEPTED,
                "invited_by": trip.created_by,
            }
        )
        if tm.status != TripMember.STATUS_ACCEPTED:
            tm.status = TripMember.STATUS_ACCEPTED
            tm.save(update_fields=["status"])

        return Response({"detail": "Joined trip successfully.", "trip_id": trip.id})


class TripDayAddAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_id: int):
        trip = get_object_or_404(Trip, id=trip_id)
        if not CanEditTrip().has_object_permission(request, self, trip):
            return Response({"detail": "No edit permission."}, status=403)

        day_number = request.data.get("day_number")
        date = request.data.get("date")
        title = request.data.get("title", "")

        if not day_number:
            last = TripDay.objects.filter(trip=trip).order_by("-day_number").first()
            day_number = (last.day_number + 1) if last else 1

        serializer = TripDaySerializer(data={"day_number": day_number, "date": date, "title": title})
        serializer.is_valid(raise_exception=True)

        day, created = TripDay.objects.get_or_create(
            trip=trip,
            day_number=serializer.validated_data["day_number"],
            defaults={
                "date": serializer.validated_data.get("date"),
                "title": serializer.validated_data.get("title", ""),
            }
        )
        if not created:
            # allow patching title/date if already exists
            day.date = serializer.validated_data.get("date", day.date)
            day.title = serializer.validated_data.get("title", day.title)
            day.save()

        return Response(TripDaySerializer(day).data, status=201)


class TripActivityAddAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_id: int):
        trip = get_object_or_404(Trip, id=trip_id)
        if not CanEditTrip().has_object_permission(request, self, trip):
            return Response({"detail": "No edit permission."}, status=403)

        day_number = request.data.get("day")
        if not day_number:
            return Response({"detail": "day is required (e.g., 1,2,3)."}, status=400)

        day = TripDay.objects.filter(trip=trip, day_number=day_number).first()
        if not day:
            day = TripDay.objects.create(trip=trip, day_number=day_number)

        payload = {
            "day": day.id,
            "title": request.data.get("title", ""),
            "location_name": request.data.get("location_name", ""),
            "start_time": request.data.get("start_time"),
            "sort_order": request.data.get("sort_order", 1),
        }
        serializer = TripActivitySerializer(data=payload)
        serializer.is_valid(raise_exception=True)

        activity = TripActivity.objects.create(
            trip=trip,
            day=day,
            title=serializer.validated_data["title"],
            location_name=serializer.validated_data.get("location_name", ""),
            start_time=serializer.validated_data.get("start_time"),
            sort_order=serializer.validated_data.get("sort_order", 1),
            created_by=request.user,
        )

        # return enriched response
        out = TripActivitySerializer(activity).data
        out["likes_count"] = 0
        out["comments_count"] = 0
        return Response(out, status=201)


class TripActivityUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, activity_id: int):
        activity = get_object_or_404(TripActivity, id=activity_id)
        if not CanEditTrip().has_object_permission(request, self, activity):
            return Response({"detail": "No edit permission."}, status=403)

        fields = ["title", "location_name", "start_time", "sort_order"]
        for f in fields:
            if f in request.data:
                setattr(activity, f, request.data.get(f))
        activity.save()

        data = TripActivitySerializer(activity).data
        data["likes_count"] = activity.reactions.count()
        data["comments_count"] = activity.messages.count()
        return Response(data)


class TripActivityDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, activity_id: int):
        activity = get_object_or_404(TripActivity, id=activity_id)
        if not CanEditTrip().has_object_permission(request, self, activity):
            return Response({"detail": "No edit permission."}, status=403)

        activity.delete()
        return Response(status=204)


class ActivityMessagesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, activity_id: int):
        activity = get_object_or_404(TripActivity, id=activity_id)
        if not get_membership(request.user, activity.trip):
            return Response({"detail": "Not a trip member."}, status=403)

        msgs = ActivityMessage.objects.filter(activity=activity).select_related("user")
        return Response(ActivityMessageSerializer(msgs, many=True).data)


class ActivityMessageAddAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, activity_id: int):
        activity = get_object_or_404(TripActivity, id=activity_id)
        if not CanEditTrip().has_object_permission(request, self, activity.trip):
            return Response({"detail": "No edit permission."}, status=403)

        message = request.data.get("message", "").strip()
        if not message:
            return Response({"detail": "message is required."}, status=400)

        msg = ActivityMessage.objects.create(activity=activity, user=request.user, message=message)
        return Response(ActivityMessageSerializer(msg).data, status=201)


class ActivityLikeToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, activity_id: int):
        activity = get_object_or_404(TripActivity, id=activity_id)
        if not get_membership(request.user, activity.trip):
            return Response({"detail": "Not a trip member."}, status=403)

        obj = ActivityReaction.objects.filter(activity=activity, user=request.user).first()
        if obj:
            obj.delete()
            liked = False
        else:
            ActivityReaction.objects.create(activity=activity, user=request.user)
            liked = True

        return Response({
            "liked": liked,
            "likes_count": activity.reactions.count()
        })
