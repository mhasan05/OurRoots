from rest_framework import serializers
from .models import Quiz, Question, Option, UserAnswer

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = "__all__"

class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True)

    class Meta:
        model = Question
        fields = "__all__"

class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)

    class Meta:
        model = Quiz
        fields = "__all__"

class UserAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnswer
        fields = "__all__"



class QuizCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = (
            "id",
            "title",
            "subtitle",
            "description",
            "is_published",
        )


class QuestionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = (
            "id",
            "quiz",
            "question_text",
            "question_type",
            "order_index",
            "points",
        )


class OptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = (
            "id",
            "question",
            "option_text",
            "is_correct",
            "order_index",
        )

