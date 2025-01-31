from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Profile, School


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['name', 'phone_number', 'school', 'class_number', 'class_letter']

    def generate_username(self, phone_number):
        return f"user{phone_number}"

    def create(self, validated_data):
        name = validated_data.pop('name')
        class_number = validated_data.pop('class_number')
        class_letter = validated_data.pop('class_letter')
        school = validated_data.pop('school')
        phone_number = validated_data.pop('phone_number')

        username = self.generate_username(phone_number)

        user = User.objects.create(
            username=username,
        )

        Profile.objects.create(
            user=user,
            name=name,
            phone_number=phone_number,
            school=school,
            class_number=class_number,
            class_letter=class_letter,
        )

        return user


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)
    def validate(self, data):
        phone_number = data.get('phone_number')
        try:
            profile = Profile.objects.get(phone_number=phone_number)
            user = profile.user
        except Profile.DoesNotExist:
            raise AuthenticationFailed('Invalid phone number.')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        return {
            "token": token,
        }


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = '__all__'
