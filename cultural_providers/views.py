from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *



class ProviderProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        provider = CulturalProvider.objects.filter(user=request.user).first()
        serializer = CulturalProviderSerializer(provider, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data)


class ProviderListAPIView(APIView):
    def get(self, request):
        providers = CulturalProvider.objects.filter(is_active=True, is_verified=True)
        return Response(CulturalProviderSerializer(providers, many=True).data)


class CreateExperienceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        provider = get_object_or_404(CulturalProvider, user=request.user)
        serializer = ExperienceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(provider=provider)
        return Response(serializer.data, status=201)

class CreateBookingAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=201)


class AddReviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=201)




class AllProvidersAPIView(APIView):

    def get(self, request):
        providers = CulturalProvider.objects.filter(
            is_active=True,
            is_verified=True,
        ).select_related("providerstats")

        serializer = CulturalProviderListSerializer(providers, many=True)
        return Response(serializer.data)



class ProviderDetailAPIView(APIView):

    def get(self, request, provider_id):
        provider = get_object_or_404(
            CulturalProvider,
            id=provider_id,
            is_active=True,
        )

        serializer = CulturalProviderDetailSerializer(provider)
        return Response(serializer.data)
