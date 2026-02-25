from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import SubscriptionPlan, UserSubscription, SubscriptionPayment


# -------------------------
# Helper: current subscription
# -------------------------

def get_active_subscription(user):
    sub = (
        UserSubscription.objects
        .filter(user=user, status="active")
        .order_by("-created_on")
        .first()
    )
    if sub and sub.is_active:
        return sub
    return None


def user_has_premium(user) -> bool:
    sub = get_active_subscription(user)
    return bool(sub and sub.plan.can_access_premium_content)


# -------------------------
# Public: List plans
# -------------------------

class SubscriptionPlanListAPIView(APIView):
    """
    GET /api/subscriptions/plans/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by("price_usd", "id")
        data = []
        for p in plans:
            data.append({
                "id": p.id,
                "tier": p.tier,
                "name": p.name,
                "description": p.description,
                "price_usd_month": float(p.price_usd),
                "is_most_popular": p.is_most_popular,
                "entitlements": {
                    "can_access_premium_content": p.can_access_premium_content,
                    "can_plan_trip_together": p.can_plan_trip_together,
                    "can_use_budget_guide": p.can_use_budget_guide,
                    "can_access_audio_guides": p.can_access_audio_guides,
                }
            })
        return Response({"plans": data})


# -------------------------
# Auth: My subscription
# -------------------------

class MySubscriptionAPIView(APIView):
    """
    GET /api/subscriptions/me/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sub = get_active_subscription(request.user)
        if not sub:
            return Response({"active": False, "subscription": None})

        return Response({
            "active": True,
            "subscription": {
                "id": sub.id,
                "status": sub.status,
                "plan": {
                    "id": sub.plan.id,
                    "tier": sub.plan.tier,
                    "name": sub.plan.name,
                    "price_usd_month": float(sub.plan.price_usd),
                    "entitlements": {
                        "can_access_premium_content": sub.plan.can_access_premium_content,
                        "can_plan_trip_together": sub.plan.can_plan_trip_together,
                        "can_use_budget_guide": sub.plan.can_use_budget_guide,
                        "can_access_audio_guides": sub.plan.can_access_audio_guides,
                    }
                },
                "current_period_start": sub.current_period_start,
                "current_period_end": sub.current_period_end,
                "cancel_at_period_end": sub.cancel_at_period_end,
            }
        })


# -------------------------
# Auth: Subscribe (manual demo)
# -------------------------

class SubscribeAPIView(APIView):
    """
    POST /api/subscriptions/subscribe/
    Body:
    {
      "plan_id": 3,
      "months": 1,
      "payment_method": "stripe"   // just stored for now
    }

    NOTE: This is a "manual subscription activation" flow.
    Stripe Checkout can be integrated later; this API still works.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get("plan_id")
        months = int(request.data.get("months") or 1)
        months = max(1, min(months, 24))

        payment_method = (request.data.get("payment_method") or "manual").lower()

        plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)

        # Free plan can be activated without payment record
        now = timezone.now()
        period_end = now + timedelta(days=30 * months)

        with transaction.atomic():
            # cancel previous active subs
            UserSubscription.objects.filter(user=request.user, status="active").update(
                status="canceled",
                canceled_at=now,
                cancel_at_period_end=False,
            )

            sub = UserSubscription.objects.create(
                user=request.user,
                plan=plan,
                status="active",
                started_at=now,
                current_period_start=now,
                current_period_end=period_end,
                provider=payment_method,
            )

            # create payment record for non-free plans
            if plan.price_usd > 0:
                amount = plan.price_usd * months
                SubscriptionPayment.objects.create(
                    user=request.user,
                    subscription=sub,
                    plan=plan,
                    amount=amount,
                    currency="USD",
                    status="paid",  # in real Stripe: pending until webhook confirms
                    provider=payment_method,
                    paid_at=now,
                )

        return Response({
            "detail": "Subscription activated",
            "subscription_id": sub.id,
            "plan": {"id": plan.id, "tier": plan.tier, "name": plan.name},
            "current_period_end": sub.current_period_end
        }, status=201)


# -------------------------
# Auth: Cancel at period end
# -------------------------

class CancelSubscriptionAPIView(APIView):
    """
    POST /api/subscriptions/cancel/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        sub = get_active_subscription(request.user)
        if not sub:
            return Response({"detail": "No active subscription."}, status=400)

        sub.cancel_at_period_end = True
        sub.save(update_fields=["cancel_at_period_end", "updated_on"])
        return Response({"detail": "Cancellation scheduled at period end."})


# -------------------------
# Auth: Payments list
# -------------------------

class MyPaymentsAPIView(APIView):
    """
    GET /api/subscriptions/payments/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = SubscriptionPayment.objects.filter(user=request.user).order_by("-created_on")[:50]
        data = []
        for p in payments:
            data.append({
                "id": p.id,
                "plan": {"tier": p.plan.tier, "name": p.plan.name},
                "amount": float(p.amount),
                "currency": p.currency,
                "status": p.status,
                "provider": p.provider,
                "paid_at": p.paid_at,
                "created_on": p.created_on,
            })
        return Response({"payments": data})
    



class IsStaffUser(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and bool(request.user and request.user.is_staff)


def _bool(v, default=False):
    if v is None:
        return default
    return str(v).lower() in ("true", "1", "yes", "y", "on")


def _plan_payload(plan: SubscriptionPlan):
    return {
        "id": plan.id,
        "tier": plan.tier,
        "name": plan.name,
        "description": plan.description,
        "price_usd": float(plan.price_usd),
        "is_active": plan.is_active,
        "is_most_popular": plan.is_most_popular,
        "entitlements": {
            "can_access_premium_content": plan.can_access_premium_content,
            "can_plan_trip_together": plan.can_plan_trip_together,
            "can_use_budget_guide": plan.can_use_budget_guide,
            "can_access_audio_guides": plan.can_access_audio_guides,
        }
    }


class AdminPlanCreateAPIView(APIView):
    """
    POST /api/subscriptions/admin/plans/
    Staff-only plan creation.
    """
    permission_classes = [IsStaffUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request):
        tier = (request.data.get("tier") or "").strip().lower()
        name = (request.data.get("name") or "").strip()

        if tier not in ("free", "community", "preparation", "premium"):
            return Response({"detail": "Invalid tier"}, status=400)

        if not name:
            return Response({"detail": "name is required"}, status=400)

        if SubscriptionPlan.objects.filter(tier=tier).exists():
            return Response({"detail": "tier already exists"}, status=400)

        plan = SubscriptionPlan.objects.create(
            tier=tier,
            name=name,
            description=request.data.get("description", ""),
            price_usd=request.data.get("price_usd") or 0,

            is_active=_bool(request.data.get("is_active"), True),
            is_most_popular=_bool(request.data.get("is_most_popular"), False),

            can_access_premium_content=_bool(request.data.get("can_access_premium_content"), False),
            can_plan_trip_together=_bool(request.data.get("can_plan_trip_together"), False),
            can_use_budget_guide=_bool(request.data.get("can_use_budget_guide"), False),
            can_access_audio_guides=_bool(request.data.get("can_access_audio_guides"), False),
        )

        return Response(_plan_payload(plan), status=201)


class AdminPlanUpdateAPIView(APIView):
    """
    PATCH /api/subscriptions/admin/plans/<id>/
    """
    permission_classes = [IsStaffUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def patch(self, request, plan_id: int):
        plan = get_object_or_404(SubscriptionPlan, id=plan_id)

        if "tier" in request.data:
            tier = (request.data.get("tier") or "").strip().lower()
            if tier not in ("free", "community", "preparation", "premium"):
                return Response({"detail": "Invalid tier"}, status=400)
            if SubscriptionPlan.objects.exclude(id=plan.id).filter(tier=tier).exists():
                return Response({"detail": "tier already exists"}, status=400)
            plan.tier = tier

        if "name" in request.data:
            plan.name = (request.data.get("name") or "").strip()

        if "description" in request.data:
            plan.description = request.data.get("description", "")

        if "price_usd" in request.data:
            plan.price_usd = request.data.get("price_usd") or 0

        if "is_active" in request.data:
            plan.is_active = _bool(request.data.get("is_active"))

        if "is_most_popular" in request.data:
            plan.is_most_popular = _bool(request.data.get("is_most_popular"))

        # entitlements
        for field in (
            "can_access_premium_content",
            "can_plan_trip_together",
            "can_use_budget_guide",
            "can_access_audio_guides",
        ):
            if field in request.data:
                setattr(plan, field, _bool(request.data.get(field)))

        plan.save()
        return Response(_plan_payload(plan))


class AdminPlanDeleteAPIView(APIView):
    """
    DELETE /api/subscriptions/admin/plans/<id>/
    """
    permission_classes = [IsStaffUser]

    def delete(self, request, plan_id: int):
        plan = get_object_or_404(SubscriptionPlan, id=plan_id)
        plan.delete()
        return Response(status=204)


class AdminPlanListAPIView(APIView):
    """
    GET /api/subscriptions/admin/plans/
    Staff list (includes inactive)
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        plans = SubscriptionPlan.objects.all().order_by("price_usd", "id")
        return Response({"plans": [_plan_payload(p) for p in plans]})