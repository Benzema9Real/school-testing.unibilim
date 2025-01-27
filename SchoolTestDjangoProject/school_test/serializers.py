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
        not_correct_answers_count = 0
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
            if not is_correct:
                not_correct_answers_count += 1

            Answer.objects.create(
                student=user,
                test=test,
                question=question,
                selected_option=selected_option,
                is_correct=is_correct,
            )

        percentage = (correct_answers / total_questions) * 100

        result = Result.objects.create(
            student=user,
            test=test,
            percentage=percentage,
        )

        test_history, created = TestHistory.objects.get_or_create(student=user)
        test_history.results.add(result)
        test_history.save()

        user_results = test_history.results.all()
        average_user_percentage = sum(r.percentage for r in user_results) / user_results.count()
        test_history.average_percentage = average_user_percentage
        test_history.save()

        school = user.profile.school
        school_history, created = SchoolHistory.objects.get_or_create(school=school)
        school_history.results.add(result)
        school_results = school_history.results.all()

        average_school_percentage = sum(r.percentage for r in school_results) / school_results.count()
        school_history.average_percentage = average_school_percentage
        school_history.save()

        result.mistakes.set(mistakes)
        return result
