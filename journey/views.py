from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import (
    JourneyStage, GuidedExercise, ReadinessChecklistItem,
    UserStageProgress, UserExerciseProgress, UserChecklistProgress
)
from .serializers import (
    JourneyStageListSerializer, StageDetailSerializer,
    UpdateStageProgressSerializer, ToggleExerciseSerializer, ToggleChecklistSerializer
)


def _ensure_stage_progress(user, stage):
    prog, _ = UserStageProgress.objects.get_or_create(user=user, stage=stage)
    return prog


class JourneyOverviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stages = JourneyStage.objects.filter(is_active=True).order_by("number")
        return Response(JourneyStageListSerializer(stages, many=True, context={"request": request}).data)


class StageDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, stage_number: int):
        stage = get_object_or_404(JourneyStage, number=stage_number, is_active=True)
        _ensure_stage_progress(request.user, stage)
        return Response(StageDetailSerializer(stage, context={"request": request}).data)


class UpdateStageProgressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, stage_number: int):
        stage = get_object_or_404(JourneyStage, number=stage_number, is_active=True)
        serializer = UpdateStageProgressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        prog = _ensure_stage_progress(request.user, stage)
        prog.percent_complete = serializer.validated_data["percent_complete"]

        # mark complete automatically at 100%
        if prog.percent_complete >= 100 and not prog.completed_at:
            prog.completed_at = timezone.now()
        if prog.percent_complete < 100:
            prog.completed_at = None

        prog.save()
        return Response({
            "stage": stage.number,
            "percent_complete": prog.percent_complete,
            "is_completed": bool(prog.completed_at),
        })


class ToggleExerciseCompletionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, exercise_id: int):
        exercise = get_object_or_404(GuidedExercise, id=exercise_id)
        stage = exercise.stage

        serializer = ToggleExerciseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_completed = serializer.validated_data["is_completed"]

        obj, _ = UserExerciseProgress.objects.get_or_create(user=request.user, exercise=exercise)
        obj.is_completed = is_completed
        obj.completed_at = timezone.now() if is_completed else None
        obj.save()

        # OPTIONAL: auto-recompute stage percent from exercises+checklist
        self._recompute_stage_percent(request.user, stage)

        return Response({
            "exercise_id": exercise.id,
            "is_completed": obj.is_completed,
        }, status=200)

    def _recompute_stage_percent(self, user, stage):
        exercises = stage.exercises.count()
        checklist = stage.checklist_items.count()
        total = exercises + checklist
        if total == 0:
            return

        done_ex = UserExerciseProgress.objects.filter(user=user, exercise__stage=stage, is_completed=True).count()
        done_ck = UserChecklistProgress.objects.filter(user=user, item__stage=stage, is_checked=True).count()
        percent = int(((done_ex + done_ck) / total) * 100)

        prog = _ensure_stage_progress(user, stage)
        prog.percent_complete = max(prog.percent_complete, percent)  # keep highest
        if prog.percent_complete >= 100 and not prog.completed_at:
            prog.completed_at = timezone.now()
        prog.save()


class ToggleChecklistItemAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, item_id: int):
        item = get_object_or_404(ReadinessChecklistItem, id=item_id)
        stage = item.stage

        serializer = ToggleChecklistSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_checked = serializer.validated_data["is_checked"]

        obj, _ = UserChecklistProgress.objects.get_or_create(user=request.user, item=item)
        obj.is_checked = is_checked
        obj.updated_at = timezone.now()
        obj.save()

        # OPTIONAL: same recompute logic
        exercises = stage.exercises.count()
        checklist = stage.checklist_items.count()
        total = exercises + checklist
        if total > 0:
            done_ex = UserExerciseProgress.objects.filter(user=request.user, exercise__stage=stage, is_completed=True).count()
            done_ck = UserChecklistProgress.objects.filter(user=request.user, item__stage=stage, is_checked=True).count()
            percent = int(((done_ex + done_ck) / total) * 100)

            prog = _ensure_stage_progress(request.user, stage)
            prog.percent_complete = max(prog.percent_complete, percent)
            if prog.percent_complete >= 100 and not prog.completed_at:
                prog.completed_at = timezone.now()
            if prog.percent_complete < 100:
                prog.completed_at = None
            prog.save()

        return Response({
            "item_id": item.id,
            "is_checked": obj.is_checked
        }, status=200)
