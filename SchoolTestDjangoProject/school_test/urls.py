from django.urls import path

from .views import TestListView, TestCreateView, TestDetailView, SubmitTestView, SchoolAnalyticsView, \
    StudentAnalyticsView, SubjectListView, EventListView, EventCreateView, RecommendationCreateView, \
    RecommendationListView, StudentTestHistoryView

urlpatterns = [
    path('tests/', TestListView.as_view(), name='tests'),
    path('tests/create/', TestCreateView.as_view(), name='tests_create'),
    path('tests/<int:pk>/', TestDetailView.as_view(), name='tests_id'),
    path('tests/<int:pk>/submit/', SubmitTestView.as_view(), name='tests_submit'),
    path('analytics/school/<int:id>/', SchoolAnalyticsView.as_view(), name='school_analytics'),
    path('analytics/student/<int:student_id>/', StudentAnalyticsView.as_view(), name='student_analytics'),
    path('student/test/history/<int:id>/', StudentTestHistoryView.as_view(), name='tests_id'),
    path('subject/list/', SubjectListView.as_view(), name='subject'),
    path('event/list/', EventListView.as_view(), name='event_list'),
    path('event/create/', EventCreateView.as_view(), name='event_create'),
    path('recommendation/list/', RecommendationListView.as_view(), name='recommendation_list'),
    path('recommendation/create/', RecommendationCreateView.as_view(), name='recommendation_create'),
]