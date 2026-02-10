from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Quiz, UserAnswer, Question, Option
from rest_framework import status
from django.shortcuts import get_object_or_404
from function.permissions import IsAdminUserCustom
from .serializers import *


class QuizListAPIView(APIView):
    def get(self, request):
        quizzes = Quiz.objects.filter(is_published=True)
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data)

class SubmitAnswerAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UserAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response({"message": "Answer saved"})
    


class AdminCreateQuizAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def post(self, request):
        serializer = QuizCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quiz = serializer.save(created_by=request.user)

        return Response(
            {
                "message": "Quiz created successfully",
                "quiz_id": quiz.id,
            },
            status=status.HTTP_201_CREATED,
        )



class AdminUpdateQuizAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def patch(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        serializer = QuizCreateSerializer(quiz, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "Quiz updated successfully"})




class AdminCreateQuestionAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def post(self, request):
        serializer = QuestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.save()

        return Response(
            {
                "message": "Question added successfully",
                "question_id": question.id,
            },
            status=status.HTTP_201_CREATED,
        )



class AdminUpdateQuestionAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def patch(self, request, question_id):
        question = get_object_or_404(Question, id=question_id)
        serializer = QuestionCreateSerializer(
            question, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "Question updated successfully"})


class AdminCreateOptionAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def post(self, request):
        serializer = OptionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        option = serializer.save()

        return Response(
            {
                "message": "Option added successfully",
                "option_id": option.id,
            },
            status=status.HTTP_201_CREATED,
        )



class AdminUpdateOptionAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def patch(self, request, option_id):
        option = get_object_or_404(Option, id=option_id)
        serializer = OptionCreateSerializer(
            option, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "Option updated successfully"})

