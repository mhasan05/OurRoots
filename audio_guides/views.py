from mutagen import File as MutagenFile

from django.db.models import Count
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status


from .models import AudioCategory, AudioGuide, AudioGuideProgress, AudioGuideDownload


# ---------------------------
# Helpers
# ---------------------------

def get_audio_duration_seconds(file_obj) -> int:
    """
    file_obj: file-like object (e.g., guide.audio_file.file)
    Returns int seconds; returns 0 if unknown.
    """
    if not file_obj:
        return 0

    try:
        file_obj.seek(0)
    except Exception:
        pass

    audio = MutagenFile(file_obj)
    if audio is None or not hasattr(audio, "info") or not getattr(audio.info, "length", None):
        return 0

    return int(round(audio.info.length))


class IsStaffUser(IsAuthenticated):
    """
    Staff-only permission (simple).
    """
    def has_permission(self, request, view):
        return super().has_permission(request, view) and bool(request.user and request.user.is_staff)


# ---------------------------
# Categories (Public + Admin)
# ---------------------------

class AudioCategoryListAPIView(APIView):
    """
    Public: tabs list
    GET /api/audio/categories/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        qs = (
            AudioCategory.objects.filter(is_active=True)
            .annotate(guides_count=Count("guides", distinct=True))
            .order_by("sort_order", "id")
        )
        data = []
        for c in qs:
            data.append({
                "id": c.id,
                "name": c.name,
                "slug": c.slug,
                "description": c.description,
                "sort_order": c.sort_order,
                "guides_count": c.guides_count,
            })
        return Response(data)


class AdminAudioCategoryCreateAPIView(APIView):
    """
    Staff: create category
    POST /api/audio/admin/categories/create/
    """
    permission_classes = [IsStaffUser]

    def post(self, request):
        name = (request.data.get("name") or "").strip()
        slug = (request.data.get("slug") or "").strip()
        description = request.data.get("description", "")
        sort_order = int(request.data.get("sort_order", 1))
        is_active = bool(request.data.get("is_active", True))

        if not name or not slug:
            return Response({"detail": "name and slug are required."}, status=400)

        if AudioCategory.objects.filter(slug=slug).exists():
            return Response({"detail": "slug already exists."}, status=400)

        cat = AudioCategory.objects.create(
            name=name,
            slug=slug,
            description=description,
            sort_order=sort_order,
            is_active=is_active,
        )
        return Response({
            "id": cat.id,
            "name": cat.name,
            "slug": cat.slug,
            "description": cat.description,
            "sort_order": cat.sort_order,
            "is_active": cat.is_active,
        }, status=201)


class AdminAudioCategoryUpdateAPIView(APIView):
    """
    Staff: update category
    PATCH /api/audio/admin/categories/<id>/update/
    """
    permission_classes = [IsStaffUser]

    def patch(self, request, category_id: int):
        cat = get_object_or_404(AudioCategory, id=category_id)

        if "name" in request.data:
            cat.name = (request.data.get("name") or "").strip()

        if "slug" in request.data:
            new_slug = (request.data.get("slug") or "").strip()
            if new_slug and AudioCategory.objects.exclude(id=cat.id).filter(slug=new_slug).exists():
                return Response({"detail": "slug already exists."}, status=400)
            cat.slug = new_slug

        if "description" in request.data:
            cat.description = request.data.get("description", "")

        if "sort_order" in request.data:
            cat.sort_order = int(request.data.get("sort_order") or 1)

        if "is_active" in request.data:
            cat.is_active = bool(request.data.get("is_active"))

        cat.save()
        return Response({
            "id": cat.id,
            "name": cat.name,
            "slug": cat.slug,
            "description": cat.description,
            "sort_order": cat.sort_order,
            "is_active": cat.is_active,
        })


class AdminAudioCategoryDeleteAPIView(APIView):
    """
    Staff: delete category
    DELETE /api/audio/admin/categories/<id>/delete/
    """
    permission_classes = [IsStaffUser]

    def delete(self, request, category_id: int):
        cat = get_object_or_404(AudioCategory, id=category_id)
        cat.delete()
        return Response(status=204)


# ---------------------------
# Guides (Public)
# ---------------------------

class AudioGuideListAPIView(APIView):
    """
    Public cards list
    GET /api/audio/guides/?category=<slug>&featured=true&q=search
    """
    permission_classes = [AllowAny]

    def get(self, request):
        qs = AudioGuide.objects.filter(is_active=True).select_related("category")

        category_slug = request.query_params.get("category")
        if category_slug and category_slug.lower() != "all":
            qs = qs.filter(category__slug=category_slug, category__is_active=True)

        featured = request.query_params.get("featured")
        if featured in ("true", "1", "yes"):
            qs = qs.filter(is_featured=True)

        q = request.query_params.get("q")
        if q:
            qs = qs.filter(title__icontains=q)

        qs = qs.order_by("sort_order", "-created_at", "id")

        data = []
        for g in qs:
            data.append({
                "id": g.id,
                "title": g.title,
                "subtitle": g.subtitle,
                "description": g.description,
                "category": {
                    "id": g.category_id,
                    "name": g.category.name if g.category else None,
                    "slug": g.category.slug if g.category else None,
                },
                "duration_seconds": g.duration_seconds,
                "duration_mmss": g.duration_mmss,
                "cover_image_url": request.build_absolute_uri(g.cover_image.url) if g.cover_image else None,
                "is_featured": g.is_featured,
            })
        return Response(data)


class AudioGuideDetailAPIView(APIView):
    """
    Public detail/player
    GET /api/audio/guides/<id>/
    """
    permission_classes = [AllowAny]

    def get(self, request, guide_id: int):
        g = get_object_or_404(AudioGuide, id=guide_id, is_active=True)

        # Optional: show progress if logged in
        user_progress = None
        if request.user.is_authenticated:
            p = AudioGuideProgress.objects.filter(user=request.user, guide=g).first()
            user_progress = {
                "position_seconds": p.position_seconds if p else 0,
                "is_completed": bool(p and p.is_completed),
            }

        return Response({
            "id": g.id,
            "title": g.title,
            "subtitle": g.subtitle,
            "description": g.description,
            "category": {
                "id": g.category_id,
                "name": g.category.name if g.category else None,
                "slug": g.category.slug if g.category else None,
            },
            "duration_seconds": g.duration_seconds,
            "duration_mmss": g.duration_mmss,
            "cover_image_url": request.build_absolute_uri(g.cover_image.url) if g.cover_image else None,
            "audio_file_url": request.build_absolute_uri(g.audio_file.url) if g.audio_file else None,
            "audio_url": g.audio_url or None,
            "is_featured": g.is_featured,
            "user_progress": user_progress,
        })


# ---------------------------
# Guides (Admin CRUD + Duration Auto-calc)
# ---------------------------

class AdminAudioGuideCreateAPIView(APIView):
    """
    Staff upload guide (multipart/form-data)
    POST /api/audio/admin/guides/create/
    """
    permission_classes = [IsStaffUser]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        title = (request.data.get("title") or "").strip()
        if not title:
            return Response({"detail": "title is required."}, status=400)

        guide = AudioGuide.objects.create(
            title=title,
            subtitle=request.data.get("subtitle", ""),
            description=request.data.get("description", ""),
            category_id=request.data.get("category") or None,
            cover_image=request.data.get("cover_image"),
            audio_file=request.data.get("audio_file"),
            audio_url=request.data.get("audio_url", ""),
            duration_seconds=int(request.data.get("duration_seconds") or 0),
            is_featured=str(request.data.get("is_featured", "false")).lower() in ("true", "1", "yes"),
            is_active=str(request.data.get("is_active", "true")).lower() in ("true", "1", "yes"),
            sort_order=int(request.data.get("sort_order") or 1),
        )

        # ✅ Auto-calc duration if missing and file exists
        if (not guide.duration_seconds) and guide.audio_file:
            try:
                duration = get_audio_duration_seconds(guide.audio_file.file)
                if duration > 0:
                    guide.duration_seconds = duration
                    guide.save(update_fields=["duration_seconds"])
            except Exception:
                pass

        return Response(_admin_guide_payload(request, guide), status=201)


class AdminAudioGuideUpdateAPIView(APIView):
    """
    Staff update guide (multipart allowed)
    PATCH /api/audio/admin/guides/<id>/update/
    """
    permission_classes = [IsStaffUser]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, guide_id: int):
        guide = get_object_or_404(AudioGuide, id=guide_id)

        audio_file_updated = False

        if "title" in request.data:
            guide.title = (request.data.get("title") or "").strip()

        if "subtitle" in request.data:
            guide.subtitle = request.data.get("subtitle", "")

        if "description" in request.data:
            guide.description = request.data.get("description", "")

        if "category" in request.data:
            guide.category_id = request.data.get("category") or None

        if "cover_image" in request.data:
            guide.cover_image = request.data.get("cover_image")

        if "audio_file" in request.data:
            guide.audio_file = request.data.get("audio_file")
            audio_file_updated = True

        if "audio_url" in request.data:
            guide.audio_url = request.data.get("audio_url", "")

        if "duration_seconds" in request.data:
            guide.duration_seconds = int(request.data.get("duration_seconds") or 0)

        if "is_featured" in request.data:
            guide.is_featured = str(request.data.get("is_featured")).lower() in ("true", "1", "yes")

        if "is_active" in request.data:
            guide.is_active = str(request.data.get("is_active")).lower() in ("true", "1", "yes")

        if "sort_order" in request.data:
            guide.sort_order = int(request.data.get("sort_order") or 1)

        guide.save()

        # ✅ Recalc duration if audio updated OR duration missing
        if (audio_file_updated or not guide.duration_seconds) and guide.audio_file:
            try:
                duration = get_audio_duration_seconds(guide.audio_file.file)
                if duration > 0:
                    guide.duration_seconds = duration
                    guide.save(update_fields=["duration_seconds"])
            except Exception:
                pass

        return Response(_admin_guide_payload(request, guide), status=200)


class AdminAudioGuideDeleteAPIView(APIView):
    """
    Staff delete guide
    DELETE /api/audio/admin/guides/<id>/delete/
    """
    permission_classes = [IsStaffUser]

    def delete(self, request, guide_id: int):
        guide = get_object_or_404(AudioGuide, id=guide_id)
        guide.delete()
        return Response(status=204)


def _admin_guide_payload(request, guide: AudioGuide):
    return {
        "id": guide.id,
        "title": guide.title,
        "subtitle": guide.subtitle,
        "description": guide.description,
        "category": guide.category_id,
        "cover_image": guide.cover_image.url if guide.cover_image else None,
        "audio_file": guide.audio_file.url if guide.audio_file else None,
        "audio_url": guide.audio_url,
        "duration_seconds": guide.duration_seconds,
        "is_featured": guide.is_featured,
        "is_active": guide.is_active,
        "sort_order": guide.sort_order,
    }


# ---------------------------
# Auth-only: progress + download
# ---------------------------

class AudioGuideSaveProgressAPIView(APIView):
    """
    POST /api/audio/guides/<id>/progress/
    Body: { "position_seconds": 95, "is_completed": false }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, guide_id: int):
        guide = get_object_or_404(AudioGuide, id=guide_id, is_active=True)

        position = int(request.data.get("position_seconds") or 0)
        is_completed = bool(request.data.get("is_completed", False))

        if guide.duration_seconds and position > guide.duration_seconds:
            position = guide.duration_seconds

        obj, _ = AudioGuideProgress.objects.get_or_create(user=request.user, guide=guide)
        obj.position_seconds = max(position, 0)
        obj.is_completed = is_completed
        obj.save()

        return Response({
            "guide_id": guide.id,
            "position_seconds": obj.position_seconds,
            "is_completed": obj.is_completed
        }, status=200)


class AudioGuideDownloadAPIView(APIView):
    """
    GET /api/audio/guides/<id>/download/
    - tracks download
    - returns file stream if audio_file exists
    - otherwise returns {download_url: audio_url}
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, guide_id: int):
        guide = get_object_or_404(AudioGuide, id=guide_id, is_active=True)
        AudioGuideDownload.objects.create(guide=guide, user=request.user)

        if guide.audio_file:
            try:
                resp = FileResponse(guide.audio_file.open("rb"), as_attachment=True)
                resp["Content-Disposition"] = f'attachment; filename="{guide.title}.mp3"'
                return resp
            except FileNotFoundError:
                raise Http404("Audio file not found")

        if guide.audio_url:
            return Response({"download_url": guide.audio_url}, status=200)

        return Response({"detail": "No downloadable source available."}, status=404)
