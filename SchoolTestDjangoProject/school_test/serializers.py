from rest_framework import serializers
from .models import Answer, Test, Question, AnswerOption, Result, Event, Subject, Recommendation, TestHistory, \
    SchoolHistory


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'


class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommendation
        fields = '__all__'
        read_only_fields = ['created_at']


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'


class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = '__all__'


class StudentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TestHistory
        fields = '__all__'


class AnalyticSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestHistory
        fields = ['average_percentage', 'full_name', 'total_questions_history', 'all_mistakes']


class SchoolHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolHistory
        fields = '__all__'


class QuestionSerializer(serializers.ModelSerializer):
    options = AnswerOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = '__all__'


class TestListSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Test
        fields = '__all__'


class TestCreateSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Test
        fields = ['id', 'subject', 'name', 'school', 'description', 'questions']
        read_only_fields = ['created_by']


class TestResultSerializer(serializers.ModelSerializer):
    mistakes = serializers.StringRelatedField(many=True)

    class Meta:
        model = Result
        fields = '__all__'


class TestSubmissionSerializer(serializers.Serializer):
    answers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField(),
            help_text="Список словарей с ключами: 'question_id' и 'selected_option_id'."
                      "Пример для Амантура:{ answers: [{ question_id: 1, selected_option_id: 4},{ question_id: 2,selected_option_id: 8}    ]}"
        )
    )

    def validate(self, data):
        test_id = self.context['test_id']
        answers = data['answers']

        try:
            test = Test.objects.get(id=test_id)
        except Test.DoesNotExist:
            raise serializers.ValidationError(f"Тест с ID {test_id} не найден.")

        question_ids = set(q.id for q in test.questions.all())
        provided_question_ids = {answer['question_id'] for answer in answers}

        missing_questions = question_ids - provided_question_ids
        if missing_questions:
            missing_question_texts = [
                Question.objects.get(id=question_id).text for question_id in missing_questions
            ]
            raise serializers.ValidationError({
                "answers": f"Вы не ответили на следующие вопросы: {', '.join(missing_question_texts)}"
            })

        for answer in answers:
            if answer['question_id'] not in question_ids:
                raise serializers.ValidationError(f"Вопрос с ID {answer['question_id']} не принадлежит тесту.")

        return data


class ResultSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = ['id', 'test', 'student', 'percentage', 'mistakes']
        read_only_fields = ['student', 'test']
