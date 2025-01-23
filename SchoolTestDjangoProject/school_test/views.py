from rest_framework import status
from .models import Test, Question, Answer, Result, AnswerOption, Subject, Event, Recommendation, TestHistory, \
    SchoolHistory
from .serializers import TestListSerializer, TestSubmissionSerializer, TestResultSerializer, TestCreateSerializer, \
    SubjectSerializer, EventSerializer, RecommendationSerializer, StudentHistorySerializer, SchoolHistorySerializer
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import User, Test, Result, Answer
from rest_framework import generics, status
from rest_framework.response import Response
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
        serializer = self.get_serializer(data=request.data, context={'request': request, 'test_id': test_id})

        if serializer.is_valid():
            # Сначала сохраняем результат
            result = serializer.save()

            # Сохраняем результат, чтобы он получил ID
            result.save()

            # Теперь добавляем результат в историю тестов
            test_history, _ = TestHistory.objects.get_or_create(student=result.student)
            test_history.results.add(result)  # Добавляем результат после сохранения
            test_history.save()

            # Если студент связан с школой, обновляем SchoolHistory
            if result.student.profile.school:
                school = result.student.profile.school
                school_history, _ = SchoolHistory.objects.get_or_create(school=school)
                school_history.save()

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






class SchoolAnalyticsView(generics.ListAPIView):
    queryset = SchoolHistory.objects.all()
    serializer_class = SchoolHistorySerializer
    permission_classes = [IsAuthenticated]


class StudentAnalyticsView():
    serializer_class = StudentHistorySerializer
    permission_classes = [IsAuthenticated]


class StudentTestHistoryView(generics.ListAPIView):
    queryset = TestHistory.objects.all()
    serializer_class = StudentHistorySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'student_id'

    def get_queryset(self):
        student_id = self.kwargs['student_id']


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
        class_number = request.data.get('class_number')
        min_percentage = request.data.get('min_percentage')
        max_percentage = request.data.get('max_percentage')
        message = request.data.get('message')
        link = request.data.get('link')
        school = request.data.get('school')
        subject = request.data.get('subject')

        try:

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
            school_id = request.data.get('school')
            school = School.objects.get(id=school_id)
            subject_id = request.data.get('school')
            subject = Subject.objects.get(id=subject_id)
            recommendation = Recommendation.objects.create(
                school=school,
                class_number=class_number,
                min_percentage=min_percentage,
                max_percentage=max_percentage,
                message=message,
                link=link,
                subject=subject
            )

            return Response(
                {'status': 'Сообщение успешно отправлено.',
                 'total_students': results.count()

                 },
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
