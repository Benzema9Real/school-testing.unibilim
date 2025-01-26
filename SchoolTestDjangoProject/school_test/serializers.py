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
        fields = ['average_percentage','full_name','total_questions_history','all_mistakes']
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


class TestSubmissionSerializer(serializers.Serializer):
    answers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField(),
            help_text="Список словарей с ключами: 'question_id' и 'selected_option_id'."
                      "Пример для Амантура:{ answers: [{ question_id: 1, selected_option_id: 4},{ question_id: 2,selected_option_id: 8}    ]}"
        )
    )

    def create(self, validated_data):
        user = self.context['request'].user
        test_id = self.context['test_id']
        test = Test.objects.get(id=test_id)
        answers_data = validated_data['answers']

        correct_answers = 0
        total_questions = test.questions.count()


        for answer_data in answers_data:
            question = Question.objects.get(id=answer_data['question_id'])
            selected_option = AnswerOption.objects.get(id=answer_data['selected_option_id'])

            is_correct = selected_option.is_correct


            Answer.objects.create(
                student=user,
                test=test,
                question=question,
                selected_option=selected_option,
                is_correct=is_correct
            )

            if is_correct:
                correct_answers += 1

        percentage = (correct_answers / total_questions) * 100


        result = Result.objects.create(
            student=user,
            test=test,
            percentage=percentage
        )


        return result




class TestResultSerializer(serializers.ModelSerializer):
    mistakes = serializers.StringRelatedField(many=True)

    class Meta:
        model = Result
        fields = '__all__'





