from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import (
    BudgetStyle, BudgetExperience, BudgetCategoryRule,
    BudgetSession, BudgetSessionExperience, BudgetSessionBreakdown,
    BudgetResource, BudgetShare
)
from .serializers import (
    BudgetStyleSerializer, BudgetExperienceSerializer, CategoryRuleSerializer,
    BudgetSessionSerializer, BudgetResourceSerializer,
    SetStyleSerializer, SetDurationSerializer, SetExperiencesSerializer,
    UpdateBreakdownSerializer, ShareWithProviderSerializer
)
from .services import generate_default_breakdown, compute_experiences_cost


def _get_or_create_active_session(user):
    # simplest: one active session (latest)
    session = BudgetSession.objects.filter(user=user).order_by("-updated_at").first()
    if not session:
        session = BudgetSession.objects.create(user=user, current_step=1, days=7)
    return session


class BudgetMetaAPIView(APIView):
    """
    Returns right-side resources + styles + experiences (for wizard screens).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        styles = BudgetStyle.objects.filter(is_active=True).order_by("sort_order")
        experiences = BudgetExperience.objects.filter(is_active=True).order_by("sort_order")
        resources = BudgetResource.objects.filter(is_active=True).order_by("sort_order")

        return Response({
            "styles": BudgetStyleSerializer(styles, many=True).data,
            "experiences": BudgetExperienceSerializer(experiences, many=True).data,
            "resources": BudgetResourceSerializer(resources, many=True).data,
        })


class BudgetSessionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        session = _get_or_create_active_session(request.user)
        return Response(BudgetSessionSerializer(session).data)

    def post(self, request):
        """
        Start fresh session (optional).
        """
        session = BudgetSession.objects.create(user=request.user, current_step=1, days=7)
        return Response(BudgetSessionSerializer(session).data, status=201)


class SetStyleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session = _get_or_create_active_session(request.user)
        serializer = SetStyleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        style = get_object_or_404(BudgetStyle, key=serializer.validated_data["style_key"], is_active=True)
        session.style = style
        session.current_step = max(session.current_step, 1)
        session.save(update_fields=["style", "current_step"])

        # After style set, return category rules hints too
        rules = BudgetCategoryRule.objects.filter(style=style)
        return Response({
            "session": BudgetSessionSerializer(session).data,
            "category_rules": CategoryRuleSerializer(rules, many=True).data,
        })


class SetDurationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session = _get_or_create_active_session(request.user)
        serializer = SetDurationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session.days = serializer.validated_data["days"]
        session.current_step = max(session.current_step, 2)
        session.save(update_fields=["days", "current_step"])
        return Response(BudgetSessionSerializer(session).data)


class SetExperiencesAPIView(APIView):
    """
    Step-3: user selects experiences with quantity
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session = _get_or_create_active_session(request.user)
        if not session.style:
            return Response({"detail": "Select travel style first."}, status=400)

        serializer = SetExperiencesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items = serializer.validated_data["experiences"]

        with transaction.atomic():
            BudgetSessionExperience.objects.filter(session=session).delete()
            for item in items:
                exp_id = item.get("experience_id")
                qty = int(item.get("quantity", 1))
                if not exp_id:
                    continue
                exp = BudgetExperience.objects.filter(id=exp_id, is_active=True).first()
                if not exp:
                    continue
                BudgetSessionExperience.objects.create(session=session, experience=exp, quantity=max(qty, 1))

        session.current_step = max(session.current_step, 3)
        session.save(update_fields=["current_step"])

        # Suggest experiences cost so UI can show it
        exp_cost = compute_experiences_cost(session)
        return Response({
            "session": BudgetSessionSerializer(session).data,
            "suggested_experiences_cost": exp_cost
        })


class GenerateCostBreakdownAPIView(APIView):
    """
    Step-4: generate default breakdown using rules + selected experiences
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session = _get_or_create_active_session(request.user)
        if not session.style:
            return Response({"detail": "Select travel style first."}, status=400)

        breakdown = generate_default_breakdown(session)
        session.current_step = max(session.current_step, 4)
        session.save(update_fields=["current_step"])

        style_rules = BudgetCategoryRule.objects.filter(style=session.style)
        return Response({
            "session": BudgetSessionSerializer(session).data,
            "category_rules": CategoryRuleSerializer(style_rules, many=True).data,
        })


class UpdateBreakdownAPIView(APIView):
    """
    User edits category amounts (pencil icon).
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        session = _get_or_create_active_session(request.user)
        breakdown, _ = BudgetSessionBreakdown.objects.get_or_create(session=session)

        serializer = UpdateBreakdownSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        for field, value in serializer.validated_data.items():
            setattr(breakdown, field, value)

        breakdown.save()
        session.total_estimate = breakdown.total()
        session.current_step = max(session.current_step, 4)
        session.save(update_fields=["total_estimate", "current_step"])

        return Response(BudgetSessionSerializer(session).data)


class FinalizeBudgetAPIView(APIView):
    """
    Step-5: finalize (save to dashboard)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session = _get_or_create_active_session(request.user)
        if not hasattr(session, "breakdown"):
            return Response({"detail": "Generate cost breakdown first."}, status=400)

        session.current_step = 5
        session.total_estimate = session.breakdown.total()
        session.save(update_fields=["current_step", "total_estimate"])

        return Response({
            "detail": "Budget finalized.",
            "session": BudgetSessionSerializer(session).data
        })


class ShareWithProviderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session = _get_or_create_active_session(request.user)
        if not hasattr(session, "breakdown"):
            return Response({"detail": "Generate cost breakdown first."}, status=400)

        serializer = ShareWithProviderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        share = BudgetShare.objects.create(
            session=session,
            shared_by=request.user,
            provider_user_id=serializer.validated_data.get("provider_user_id"),
            note=serializer.validated_data.get("note", ""),
        )
        return Response({
            "detail": "Shared with provider.",
            "share_id": share.id
        }, status=201)
