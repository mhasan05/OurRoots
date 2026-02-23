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


from django.db.models import Count, Q, F, Sum
class QuizOverviewReportAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, quiz_id: int):
        quiz = get_object_or_404(Quiz, id=quiz_id)

        questions_qs = Question.objects.filter(quiz=quiz).order_by("order_index", "id")
        total_questions = questions_qs.count()
        total_points = questions_qs.aggregate(total=Sum("points"))["total"] or 0

        answers_qs = UserAnswer.objects.filter(question__quiz=quiz)
        total_answers = answers_qs.count()
        unique_users_attempted = answers_qs.values("user_id").distinct().count()


        q_attempts = dict(
            answers_qs.values("question_id").annotate(c=Count("id")).values_list("question_id", "c")
        )

        q_correct = dict(
            answers_qs.filter(option__is_correct=True)
            .values("question_id").annotate(c=Count("id"))
            .values_list("question_id", "c")
        )

        option_counts = dict(
            answers_qs.values("option_id").annotate(c=Count("id")).values_list("option_id", "c")
        )

        questions = list(
            questions_qs.prefetch_related("options")
        )

        per_question = []
        for q in questions:
            attempts = q_attempts.get(q.id, 0)
            correct = q_correct.get(q.id, 0)
            accuracy = round((correct / attempts) * 100, 2) if attempts else 0.0

            options_data = []
            for opt in q.options.all().order_by("order_index", "id"):
                selected = option_counts.get(opt.id, 0)
                pct = round((selected / attempts) * 100, 2) if attempts else 0.0
                options_data.append({
                    "option_id": opt.id,
                    "option_text": opt.option_text,
                    "is_correct": opt.is_correct,
                    "selected_count": selected,
                    "selected_percent": pct
                })

            per_question.append({
                "question_id": q.id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "order_index": q.order_index,
                "points": q.points,
                "attempts": attempts,
                "correct_attempts": correct,
                "accuracy_percent": accuracy,
                "options": options_data,
            })

        leaderboard_qs = (
            answers_qs.filter(option__is_correct=True)
            .values("user_id")
            .annotate(score=Sum("question__points"), correct_answers=Count("id"))
            .order_by("-score", "-correct_answers")[:10]
        )
        leaderboard = [
            {
                "user_id": row["user_id"],
                "score": row["score"] or 0,
                "correct_answers": row["correct_answers"],
            }
            for row in leaderboard_qs
        ]

        return Response({
            "quiz": {
                "id": quiz.id,
                "title": quiz.title,
                "subtitle": quiz.subtitle,
                "description": quiz.description,
                "is_published": quiz.is_published,
                "created_by": quiz.created_by_id,
                "created_on": quiz.created_on,
                "updated_on": quiz.updated_on,
            },
            "summary": {
                "total_questions": total_questions,
                "total_points": total_points,
                "total_answers": total_answers,
                "unique_users_attempted": unique_users_attempted,
            },
            "questions": per_question,
            "leaderboard_top10": leaderboard,
        })
    



class UserQuizSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, quiz_id: int, user_id: int):
        quiz = get_object_or_404(Quiz, id=quiz_id)

        questions = Question.objects.filter(quiz=quiz).order_by("order_index", "id")
        total_questions = questions.count()
        total_points = questions.aggregate(total=Sum("points"))["total"] or 0

        user_answers = UserAnswer.objects.filter(
            user_id=user_id,
            question__quiz=quiz
        ).select_related("question", "option")

        answered_question_ids = user_answers.values_list("question_id", flat=True).distinct()
        total_answered = len(set(answered_question_ids))

        correct_answers = user_answers.filter(option__is_correct=True)
        correct_count = correct_answers.count()

        score = correct_answers.aggregate(
            total=Sum("question__points")
        )["total"] or 0

        per_question = []
        for q in questions:
            user_q_answers = user_answers.filter(question=q)

            if not user_q_answers.exists():
                status = "skipped"
                selected_options = []
            else:
                selected_options = [
                    {
                        "option_id": ua.option.id,
                        "option_text": ua.option.option_text,
                        "is_correct": ua.option.is_correct
                    }
                    for ua in user_q_answers
                ]

                correct_options_ids = set(
                    Option.objects.filter(question=q, is_correct=True)
                    .values_list("id", flat=True)
                )

                selected_ids = set(
                    user_q_answers.values_list("option_id", flat=True)
                )

                if selected_ids == correct_options_ids:
                    status = "correct"
                else:
                    status = "wrong"

            per_question.append({
                "question_id": q.id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "points": q.points,
                "status": status,
                "selected_options": selected_options,
            })

        skipped = total_questions - total_answered
        wrong = total_answered - correct_count

        percentage = round((score / total_points) * 100, 2) if total_points else 0

        return Response({
            "quiz": {
                "id": quiz.id,
                "title": quiz.title,
            },
            "user_id": user_id,
            "summary": {
                "total_questions": total_questions,
                "answered": total_answered,
                "correct": correct_count,
                "wrong": wrong,
                "skipped": skipped,
                "total_points": total_points,
                "score": score,
                "percentage": percentage
            },
            "questions": per_question
        })
    


class MyQuizSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, quiz_id: int):
        return UserQuizSummaryAPIView().get(request, quiz_id, request.user.id)