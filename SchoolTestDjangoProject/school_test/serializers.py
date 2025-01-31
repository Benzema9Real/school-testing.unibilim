from rest_framework import serializers
from .models import Answer, Test, Question, AnswerOption, Result, Event, Subject, Recommendation, TestHistory, \
    SchoolHistory


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = '__all__'


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'


class RecommendationAllSerializer(serializers.ModelSerializer):
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


class RecommendationSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name")

    class Meta:
        model = Recommendation
        fields = ["class_number", "subject_name", "min_percentage", "max_percentage", "message", "link"]


class AnalyticSerializer(serializers.ModelSerializer):
    recommendations = serializers.SerializerMethodField()

    class Meta:
        model = TestHistory
        fields = ["average_percentage", "full_name", "recommendations"]

    def get_recommendations(self, obj):
        recommendations = Recommendation.objects.filter(
            school=obj.student.profile.school,
            min_percentage__lte=obj.average_percentage,
            max_percentage__gte=obj.average_percentage
        )
        return RecommendationSerializer(recommendations, many=True).data


class SchoolHistorySerializer(serializers.ModelSerializer):
    results_details = ResultSerializer(source='results', read_only=True)

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
        correct_answers_count = 0
        not_correct_answers_count = 0
        total_questions_count = test.questions.count()
        mistakes = []

        for answer_data in answers_data:
            question = Question.objects.get(id=answer_data['question_id'])
            selected_option = AnswerOption.objects.get(id=answer_data['selected_option_id'])

            is_correct = selected_option.is_correct
            if is_correct:
                correct_answers_count += 1
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

        percentage = (correct_answers_count / total_questions_count) * 100

        result = Result.objects.create(
            student=user,
            test=test,
            percentage=percentage,
            correct_answers_count=correct_answers_count,
            not_correct_answers_count=not_correct_answers_count,
            total_questions_count=total_questions_count
        )

        test_history, created = TestHistory.objects.get_or_create(student=user)

        if not test_history.full_name:
            test_history.full_name = user.profile.name

        test_history.results.add(result)

        user_results = test_history.results.all()
        average_user_percentage = sum(r.percentage for r in user_results) / user_results.count()
        test_history.average_percentage = average_user_percentage
        test_history.save()

        school = user.profile.school
        school_history, created = SchoolHistory.objects.get_or_create(school=school)

        student_ids = set(result.student.id for result in school_history.results.all())
        if user.id not in student_ids:
            school_history.total_students += 1

        school_history.results.add(result)

        school_results = school_history.results.all()
        average_school_percentage = sum(r.percentage for r in school_results) / school_results.count()
        school_history.average_percentage = average_school_percentage
        school_history.save()

        result.mistakes.set(mistakes)
        return result
