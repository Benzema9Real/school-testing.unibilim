from rest_framework.exceptions import NotFound
from rest_framework.generics import get_object_or_404

from .serializers import TestListSerializer, TestSubmissionSerializer, TestCreateSerializer, \
    SubjectSerializer, EventSerializer, RecommendationSerializer, SchoolHistorySerializer, AnalyticSerializer, \
    StudentHistorySerializer
from rest_framework.permissions import IsAuthenticated
from .models import User, Test, Result, Answer
from rest_framework import generics, status
from rest_framework.response import Response
from .models import Subject, Result, Recommendation, SchoolHistory, TestHistory, Event
from register.models import School


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


            event = Event.objects.filter(test=result.test, school=request.user.profile.school, class_number=request.user.profile.class_number).first()
            if event:
                event.is_completed = True
                event.save()

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


class StudentAnalyticsView(generics.RetrieveAPIView):
    queryset = TestHistory.objects.all()
    serializer_class = AnalyticSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'student_id'

    def get_queryset(self):
        student_id = self.kwargs['student_id']
        if not User.objects.filter(id=student_id).exists():
            raise NotFound(detail="  not found", code=404)
        return TestHistory.objects.filter(student_id=student_id)


class StudentTestHistoryView(generics.ListAPIView):
    queryset = TestHistory.objects.all()
    serializer_class = StudentHistorySerializer
    permission_classes = [IsAuthenticated]


class SubjectListView(generics.ListAPIView):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = []


class EventListView(generics.ListAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = []


class StudentEventListView(generics.ListAPIView):
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_profile = self.request.user.profile
        return Event.objects.filter(
            school=user_profile.school,
            class_number=user_profile.class_number
        )



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
