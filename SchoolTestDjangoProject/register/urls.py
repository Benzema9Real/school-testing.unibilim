from django.urls import path
from .views import RegisterView, LoginView, ProfileGetView, ProfileGetIdView, SchoolView

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('user/all/', ProfileGetView.as_view(), name='profile'),
    path('user/<int:pk>/', ProfileGetIdView.as_view(), name='profile_id'),
    path('school/', SchoolView.as_view(), name='school'),

]
