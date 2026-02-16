from django.db import transaction
from django.db.models import Count, Avg
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

from .models import (
    ContentCategory, ContentItem,
    ContentEnrollment, ContentBookmark, ContentRating
)


# ---------------------------
# Permissions
# ---------------------------

class IsStaffUser(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and bool(request.user and request.user.is_staff)


# ---------------------------
# Premium Check (Hook)
# ---------------------------

def user_has_premium(user) -> bool:
    """
    Replace with your real subscription logic.
    Supported patterns out-of-the-box:
      - user.is_premium
      - user.profile.is_premium
    """
    if not user or not user.is_authenticated:
        return False

    if getattr(user, "is_premium", False):
        return True

    profile = getattr(user, "profile", None)
    if profile and getattr(profile, "is_premium", False):
        return True

    return False


# ---------------------------
# Helpers
# ---------------------------

def _abs_url(request, field_file):
    if not field_file:
        return None
    return request.build_absolute_uri(field_file.url)


def _format_metric(item: ContentItem):
    """
    UI bottom-left:
    - video/audio => "45 min"
    - article => "12 min read"
    - course => "6 weeks"
    """
    if item.content_type in ("video", "audio"):
        return f"{item.duration_minutes} min" if item.duration_minutes else ""
    if item.content_type == "article":
        return f"{item.read_minutes} min read" if item.read_minutes else ""
    if item.content_type == "course":
        return f"{item.course_weeks} weeks" if item.course_weeks else ""
    return ""


def _item_card_payload(request, item: ContentItem):
    enrolled_count = item.enrollments.count()
    return {
        "id": item.id,
        "title": item.title,
        "description": item.description,
        "category": {
            "id": item.category_id,
            "name": item.category.name if item.category else None,
            "slug": item.category.slug if item.category else None,
        },
        "content_type": item.content_type,  # video/article/audio/course
        "is_premium": item.is_premium,
        "thumbnail_url": _abs_url(request, item.thumbnail),
        "metric": _format_metric(item),
        "rating_avg": float(item.rating_avg),
        "rating_count": item.rating_count,
        "enrolled_count": enrolled_count,
    }


def _recalc_rating(item: ContentItem):
    agg = item.ratings.aggregate(avg=Avg("rating"), cnt=Count("id"))
    avg = agg["avg"] or 0
    cnt = agg["cnt"] or 0
    item.rating_avg = round(float(avg), 2)
    item.rating_count = int(cnt)
    item.save(update_fields=["rating_avg", "rating_count"])


def _admin_item_payload(request, item: ContentItem):
    return {
        "id": item.id,
        "title": item.title,
        "description": item.description,
        "body_text": item.body_text,
        "category": item.category_id,
        "content_type": item.content_type,
        "thumbnail": _abs_url(request, item.thumbnail),
        "file": _abs_url(request, item.file),
        "external_url": item.external_url,
        "duration_minutes": item.duration_minutes,
        "read_minutes": item.read_minutes,
        "course_weeks": item.course_weeks,
        "is_premium": item.is_premium,
        "is_active": item.is_active,
        "sort_order": item.sort_order,
        "rating_avg": float(item.rating_avg),
        "rating_count": item.rating_count,
    }


# ---------------------------
# Public: Tabs (Categories + counts)
# ---------------------------

class ContentTabsAPIView(APIView):
    """
    GET /api/content/tabs/
    Returns tab list with counts including All Content.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        all_count = ContentItem.objects.filter(is_active=True).count()

        cats = (
            ContentCategory.objects
            .filter(is_active=True)
            .annotate(items_count=Count("items", distinct=True))
            .order_by("sort_order", "id")
        )

        tabs = [{"slug": "all", "name": "All Content", "count": all_count}]
        for c in cats:
            tabs.append({
                "id": c.id,
                "slug": c.slug,
                "name": c.name,
                "count": c.items_count,
            })

        return Response({"tabs": tabs})


# ---------------------------
# Public: Content list + Load More pagination
# ---------------------------

class ContentListAPIView(APIView):
    """
    GET /api/content/items/?category=language-learning&type=video&premium=true&q=yoruba&page=1&page_size=6
    """
    permission_classes = [AllowAny]

    def get(self, request):
        qs = ContentItem.objects.filter(is_active=True).select_related("category")

        category_slug = request.query_params.get("category")
        if category_slug and category_slug.lower() != "all":
            qs = qs.filter(category__slug=category_slug, category__is_active=True)

        ctype = request.query_params.get("type")
        if ctype in ("video", "article", "audio", "course"):
            qs = qs.filter(content_type=ctype)

        premium = request.query_params.get("premium")
        if premium in ("true", "1", "yes"):
            qs = qs.filter(is_premium=True)

        q = request.query_params.get("q")
        if q:
            qs = qs.filter(title__icontains=q)

        qs = qs.order_by("sort_order", "-created_at", "id")

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 6))
        page = max(page, 1)
        page_size = max(min(page_size, 50), 1)

        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size

        items = qs[start:end]
        data = [_item_card_payload(request, x) for x in items]
        has_next = end < total

        return Response({
            "results": data,
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_next": has_next,
            "next_page": page + 1 if has_next else None,
        })


# ---------------------------
# Public: Item detail (premium lock applied)
# ---------------------------

class ContentDetailAPIView(APIView):
    """
    GET /api/content/items/<id>/
    """
    permission_classes = [AllowAny]

    def get(self, request, item_id: int):
        item = get_object_or_404(ContentItem, id=item_id, is_active=True)

        is_locked = bool(item.is_premium and not user_has_premium(request.user))

        user_state = None
        if request.user.is_authenticated:
            user_state = {
                "is_enrolled": ContentEnrollment.objects.filter(user=request.user, item=item).exists(),
                "is_bookmarked": ContentBookmark.objects.filter(user=request.user, item=item).exists(),
                "my_rating": (
                    ContentRating.objects.filter(user=request.user, item=item)
                    .values_list("rating", flat=True)
                    .first()
                ) or None,
            }

        payload = _item_card_payload(request, item)
        payload.update({
            "is_locked": is_locked,
            # Hide direct file URL if locked
            "file_url": None if is_locked else _abs_url(request, item.file),
            # Client can use secure endpoint when unlocked
            "secure_file_url": request.build_absolute_uri(f"/api/content/items/{item.id}/file/")
            if item.file else None,
            "external_url": item.external_url or None,
            "user_state": user_state,
        })
        return Response(payload)


# ---------------------------
# Auth: Secure file streaming (premium enforced)
# ---------------------------

class ContentSecureFileAPIView(APIView):
    """
    GET /api/content/items/<id>/file/
    Returns file stream only if:
      - item is not premium OR user has premium subscription
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, item_id: int):
        item = get_object_or_404(ContentItem, id=item_id, is_active=True)

        if item.is_premium and not user_has_premium(request.user):
            return Response(
                {"detail": "Premium content. Subscription required."},
                status=status.HTTP_403_FORBIDDEN
            )

        if not item.file:
            return Response({"detail": "No file attached."}, status=status.HTTP_404_NOT_FOUND)

        try:
            return FileResponse(item.file.open("rb"), as_attachment=False)
        except FileNotFoundError:
            raise Http404("File not found")


# ---------------------------
# Auth: Enroll / Bookmark / Rate
# ---------------------------

class EnrollAPIView(APIView):
    """
    POST /api/content/items/<id>/enroll/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, item_id: int):
        item = get_object_or_404(ContentItem, id=item_id, is_active=True)
        obj, created = ContentEnrollment.objects.get_or_create(user=request.user, item=item)
        return Response({
            "item_id": item.id,
            "enrolled": True,
            "created": created,
            "enrolled_count": item.enrollments.count(),
        })


class BookmarkToggleAPIView(APIView):
    """
    POST /api/content/items/<id>/bookmark/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, item_id: int):
        item = get_object_or_404(ContentItem, id=item_id, is_active=True)

        bm = ContentBookmark.objects.filter(user=request.user, item=item).first()
        if bm:
            bm.delete()
            return Response({"item_id": item.id, "bookmarked": False})
        ContentBookmark.objects.create(user=request.user, item=item)
        return Response({"item_id": item.id, "bookmarked": True})


class RateAPIView(APIView):
    """
    POST /api/content/items/<id>/rate/
    Body: { "rating": 1..5 }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, item_id: int):
        item = get_object_or_404(ContentItem, id=item_id, is_active=True)
        rating = int(request.data.get("rating") or 0)
        if rating < 1 or rating > 5:
            return Response({"detail": "rating must be 1..5"}, status=400)

        with transaction.atomic():
            obj, _ = ContentRating.objects.get_or_create(user=request.user, item=item)
            obj.rating = rating
            obj.save()
            _recalc_rating(item)

        return Response({
            "item_id": item.id,
            "my_rating": rating,
            "rating_avg": float(item.rating_avg),
            "rating_count": item.rating_count,
        })


# ---------------------------
# Staff/Admin: Categories CRUD
# ---------------------------

class AdminCategoryCreateAPIView(APIView):
    permission_classes = [IsStaffUser]

    def post(self, request):
        name = (request.data.get("name") or "").strip()
        slug = (request.data.get("slug") or "").strip()
        if not name or not slug:
            return Response({"detail": "name and slug are required."}, status=400)

        if ContentCategory.objects.filter(slug=slug).exists():
            return Response({"detail": "slug already exists."}, status=400)

        cat = ContentCategory.objects.create(
            name=name,
            slug=slug,
            description=request.data.get("description", ""),
            sort_order=int(request.data.get("sort_order") or 1),
            is_active=str(request.data.get("is_active", "true")).lower() in ("true", "1", "yes"),
        )
        return Response({
            "id": cat.id, "name": cat.name, "slug": cat.slug,
            "description": cat.description, "sort_order": cat.sort_order, "is_active": cat.is_active
        }, status=201)


class AdminCategoryUpdateAPIView(APIView):
    permission_classes = [IsStaffUser]

    def patch(self, request, category_id: int):
        cat = get_object_or_404(ContentCategory, id=category_id)

        if "name" in request.data:
            cat.name = (request.data.get("name") or "").strip()

        if "slug" in request.data:
            new_slug = (request.data.get("slug") or "").strip()
            if new_slug and ContentCategory.objects.exclude(id=cat.id).filter(slug=new_slug).exists():
                return Response({"detail": "slug already exists."}, status=400)
            cat.slug = new_slug

        if "description" in request.data:
            cat.description = request.data.get("description", "")

        if "sort_order" in request.data:
            cat.sort_order = int(request.data.get("sort_order") or 1)

        if "is_active" in request.data:
            cat.is_active = str(request.data.get("is_active")).lower() in ("true", "1", "yes")

        cat.save()
        return Response({
            "id": cat.id, "name": cat.name, "slug": cat.slug,
            "description": cat.description, "sort_order": cat.sort_order, "is_active": cat.is_active
        })


class AdminCategoryDeleteAPIView(APIView):
    permission_classes = [IsStaffUser]

    def delete(self, request, category_id: int):
        cat = get_object_or_404(ContentCategory, id=category_id)
        cat.delete()
        return Response(status=204)


# ---------------------------
# Staff/Admin: Content CRUD (multipart)
# ---------------------------

class AdminItemCreateAPIView(APIView):
    permission_classes = [IsStaffUser]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        title = (request.data.get("title") or "").strip()
        content_type = (request.data.get("content_type") or "").strip().lower()
        if not title or content_type not in ("video", "article", "audio", "course"):
            return Response({"detail": "title and valid content_type required."}, status=400)

        item = ContentItem.objects.create(
            title=title,
            description=request.data.get("description", ""),
            body_text=request.data.get("body_text", ""),  # ✅ for read-time
            category_id=request.data.get("category") or None,
            content_type=content_type,
            thumbnail=request.data.get("thumbnail"),
            file=request.data.get("file"),
            external_url=request.data.get("external_url", ""),

            duration_minutes=int(request.data.get("duration_minutes") or 0),
            read_minutes=int(request.data.get("read_minutes") or 0),
            course_weeks=int(request.data.get("course_weeks") or 0),

            is_premium=str(request.data.get("is_premium", "false")).lower() in ("true", "1", "yes"),
            is_active=str(request.data.get("is_active", "true")).lower() in ("true", "1", "yes"),
            sort_order=int(request.data.get("sort_order") or 1),
        )

        # ✅ Models auto-calc metrics on save() if missing; but create() already saved once.
        # Force a save to run auto-metric logic if needed.
        item.save()

        return Response(_admin_item_payload(request, item), status=201)


class AdminItemUpdateAPIView(APIView):
    permission_classes = [IsStaffUser]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, item_id: int):
        item = get_object_or_404(ContentItem, id=item_id)

        if "title" in request.data:
            item.title = (request.data.get("title") or "").strip()
        if "description" in request.data:
            item.description = request.data.get("description", "")
        if "body_text" in request.data:
            item.body_text = request.data.get("body_text", "")
        if "category" in request.data:
            item.category_id = request.data.get("category") or None
        if "content_type" in request.data:
            ct = (request.data.get("content_type") or "").strip().lower()
            if ct in ("video", "article", "audio", "course"):
                item.content_type = ct
        if "thumbnail" in request.data:
            item.thumbnail = request.data.get("thumbnail")
        if "file" in request.data:
            item.file = request.data.get("file")
        if "external_url" in request.data:
            item.external_url = request.data.get("external_url", "")

        if "duration_minutes" in request.data:
            item.duration_minutes = int(request.data.get("duration_minutes") or 0)
        if "read_minutes" in request.data:
            item.read_minutes = int(request.data.get("read_minutes") or 0)
        if "course_weeks" in request.data:
            item.course_weeks = int(request.data.get("course_weeks") or 0)

        if "is_premium" in request.data:
            item.is_premium = str(request.data.get("is_premium")).lower() in ("true", "1", "yes")
        if "is_active" in request.data:
            item.is_active = str(request.data.get("is_active")).lower() in ("true", "1", "yes")
        if "sort_order" in request.data:
            item.sort_order = int(request.data.get("sort_order") or 1)

        item.save()  # ✅ triggers auto-metric if values are 0

        return Response(_admin_item_payload(request, item), status=200)


class AdminItemDeleteAPIView(APIView):
    permission_classes = [IsStaffUser]

    def delete(self, request, item_id: int):
        item = get_object_or_404(ContentItem, id=item_id)
        item.delete()
        return Response(status=204)
