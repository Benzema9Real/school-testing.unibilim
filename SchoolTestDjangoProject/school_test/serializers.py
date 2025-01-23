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

    def create(self, validated_data):
        user = self.context['request'].user
        test_id = self.context['test_id']
        test = Test.objects.get(id=test_id)
        answers_data = validated_data['answers']
        correct_answers = 0
        total_questions = test.questions.count()
        mistakes = []

        for answer_data in answers_data:
            question = Question.objects.get(id=answer_data['question_id'])
            selected_option = AnswerOption.objects.get(id=answer_data['selected_option_id'])

            is_correct = selected_option.is_correct
            if is_correct:
                correct_answers += 1
            else:
                mistakes.append(question)

            Answer.objects.create(
                student=user,
                test=test,
                question=question,
                selected_option=selected_option,
                is_correct=is_correct
            )

        percentage = (correct_answers / total_questions) * 100

        result = Result.objects.create(
            student=user,
            test=test,
            percentage=percentage,
        )
        result.mistakes.set(mistakes)
        return result


class TestResultSerializer(serializers.ModelSerializer):
    mistakes = serializers.StringRelatedField(many=True)

    class Meta:
        model = Result
        fields = '__all__'
