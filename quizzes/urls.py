from django.urls import path
from .views import *

urlpatterns = [
    path("admin/quizzes/create/", AdminCreateQuizAPIView.as_view()),
    path("admin/quizzes/<int:quiz_id>/update/", AdminUpdateQuizAPIView.as_view()),

    path("admin/questions/create/", AdminCreateQuestionAPIView.as_view()),
    path("admin/questions/<int:question_id>/update/", AdminUpdateQuestionAPIView.as_view()),

    path("admin/options/create/", AdminCreateOptionAPIView.as_view()),
    path("admin/options/<int:option_id>/update/", AdminUpdateOptionAPIView.as_view()),
    
    path("quizzes/", QuizListAPIView.as_view()),
    path("submit-answer/", SubmitAnswerAPIView.as_view()),
    path("quizzes/<int:quiz_id>/overview-report/", QuizOverviewReportAPIView.as_view()),
    path("quizzes/<int:quiz_id>/user-summary/<int:user_id>/", UserQuizSummaryAPIView.as_view()),
    path("quizzes/<int:quiz_id>/my-summary/", MyQuizSummaryAPIView.as_view()),
]
