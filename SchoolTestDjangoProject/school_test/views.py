from rest_framework import status
from .models import Test, Question, Answer, Result, AnswerOption, Subject, Event, Recommendation
from .serializers import TestListSerializer, TestSubmissionSerializer, TestResultSerializer, TestCreateSerializer, \
    SubjectSerializer, EventSerializer, RecommendationSerializer
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import User, Test, Result, Answer
from rest_framework import generics, status
from rest_framework.response import Response
from django.db.models import Q
from .models import Subject, Result, Recommendation
from .serializers import RecommendationSerializer
from register.models import School
from django.db.models import Avg


class TestListView(generics.ListAPIView):
    queryset = Test.objects.all()
    serializer_class = TestListSerializer
    permission_classes = []


class TestCreateView(generics.CreateAPIView):
    queryset = Test.objects.all()
    serializer_class = TestCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TestDetailView(generics.RetrieveAPIView):
    queryset = Test.objects.all()
    serializer_class = TestListSerializer
    permission_classes = []


class SubmitTestView(generics.GenericAPIView):
    serializer_class = TestSubmissionSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        test_id = kwargs.get('pk')
        serializer = TestSubmissionSerializer(data=request.data, context={'request': request, 'test_id': test_id})
        if serializer.is_valid():
            result = serializer.save()
            return Response({
                "message": "Тест успешно завершён.",
                "test_id": result.test.id,
                "percentage": result.percentage,
                "mistakes": [
                    {
                        "question_id": mistake.id,
                        "question_text": mistake.text
                    }
                    for mistake in result.mistakes.all()
                ]
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SchoolAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        school = get_object_or_404(School, id=id)
        total_tests = Test.objects.filter(school=school).count()
        total_questions = sum(test.questions.count() for test in school.tests.all())
        total_students = User.objects.filter(profile__school=school).count()
        average_percentage = Result.objects.filter(test__school=school).aggregate(
            avg=Avg('percentage')
        )['avg'] or 0

        total_answers = Answer.objects.filter(test__school=school).count()
        correct_answers = Answer.objects.filter(test__school=school, is_correct=True).count()
        correct_percentage = (correct_answers / total_answers * 100) if total_answers > 0 else 0
        data = {
            "Школа": school.name,
            "Количество тестов": total_tests,
            "Количество Вопросов": total_questions,
            "Количество учеников": total_students,
            "Средний процент": round(average_percentage, 2),
            "Процент правильных ответов": round(correct_percentage, 2),
        }
        return Response(data, status=200)


class StudentAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        user = get_object_or_404(User, id=id)
        student_profile = user.profile
        full_name = student_profile.name

        total_tests_taken = Result.objects.filter(student=user).count()
        average_percentage = Result.objects.filter(student=user).aggregate(
            avg=Avg('percentage')
        )['avg'] or 0
        total_answers = Answer.objects.filter(student=user).count()
        correct_answers = Answer.objects.filter(student=user, is_correct=True).count()
        correct_percentage = (correct_answers / total_answers * 100) if total_answers > 0 else 0
        recommendations = []
        results = Result.objects.filter(student=user)
        for result in results:
            recommendations_for_subject = result.test.subject.recommendation_set.all()
            for recommendation in recommendations_for_subject:
                condition = recommendation.condition.strip()
                operator = condition[:1]
                threshold = float(condition[1:])

                if operator == '<' and result.percentage < threshold:
                    recommendations.append({
                        "Предмет": recommendation.subject.name,
                        "Текст": recommendation.content,
                        "Ссылка": recommendation.link,
                    })
                elif operator == '>' and result.percentage > threshold:
                    recommendations.append({
                        "Предмет": recommendation.subject.name,
                        "Текст": recommendation.content,
                        "Ссылка": recommendation.link,
                    })

        data = {
            "ФИО ученика": full_name,
            "Количество пройденых тестов": total_tests_taken,
            "Средний процент": round(average_percentage, 2),
            "Процент правильных ответов": round(correct_percentage, 2),
            "Рекомендация": recommendations,
        }
        return Response(data, status=200)


class StudentTestHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        student = get_object_or_404(User, id=id)
        student_profile = student.profile
        full_name = student_profile.name
        results = Result.objects.filter(student=student).select_related('test', 'test__subject')

        tests_history = []
        for result in results:
            recommendations = []
            for rec in result.test.subject.recommendation_set.all():
                if eval(f"{result.percentage}{rec.condition}"):
                    recommendations.append({
                        "Текст": rec.content,
                        "link": rec.link
                    })

            tests_history.append({
                "Название теста": result.test.name,
                "Предмет": result.test.subject.name,
                "Дата прохождения": result.date_taken.strftime('%Y-%m-%d'),
                "Ошибки": [question.text for question in result.mistakes.all()],
                "Всего вопросов": result.total_questions(),
                "Правильные ответы": result.correct_answers(),
                "Процент": round(result.percentage, 2),
                "Рекомендации": recommendations
            })

        data = {
            "ФИО": full_name,
            "История прохождения тестов": tests_history
        }
        return Response(data, status=200)


class SubjectListView(generics.ListAPIView):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = []


class EventListView(generics.ListAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = []


class EventCreateView(generics.CreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = []


class RecommendationCreateView(generics.CreateAPIView):
    serializer_class = RecommendationSerializer

    def post(self, request):
        school_id = request.data.get('school_id')
        class_number = request.data.get('class_number')  # Используем class_number
        subject_id = request.data.get('subject_id')
        min_percentage = request.data.get('min_percentage')
        max_percentage = request.data.get('max_percentage')
        message = request.data.get('message')
        link = request.data.get('link')

        if not all([school_id, class_number, subject_id, min_percentage, max_percentage, message]):
            return Response({'error': 'Все поля обязательны.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            school = School.objects.get(id=school_id)
            subject = Subject.objects.get(id=subject_id)

            results = Result.objects.filter(
                test__school=school,
                test__subject=subject,
                student__profile__class_number=class_number,
                percentage__gte=min_percentage,
                percentage__lte=max_percentage,
            )

            if not results.exists():
                return Response({'error': 'Не найдено учеников, соответствующих критериям.'},
                                status=status.HTTP_404_NOT_FOUND)

            for index, result in enumerate(results, start=1):
                student = result.student
                print(f"Отправлено сообщение ученику #{index}: {student.profile.name}: {message} Ссылка: {link}")

            return Response(
                {'status': 'Сообщения успешно отправлены.', 'total_students': results.count()},
                status=status.HTTP_200_OK,
            )

        except School.DoesNotExist:
            return Response({'error': 'Указанная школа не найдена.'}, status=status.HTTP_404_NOT_FOUND)
        except Subject.DoesNotExist:
            return Response({'error': 'Указанный предмет не найден.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class RecommendationListView(generics.ListAPIView):
    queryset = Recommendation.objects.all()
    serializer_class = RecommendationSerializer
    permission_classes = []