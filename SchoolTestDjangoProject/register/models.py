from django.contrib.auth.models import AbstractUser, User
from django.db import models
from django.core.exceptions import ValidationError
import re


# Валидатор для номера телефона
def validate_kyrgyz_phone_number(value):
    kyrgyz_phone_pattern = r'^\+996\d{9}$'
    if not re.match(kyrgyz_phone_pattern, value):
        raise ValidationError('Введите корректный номер телефона в формате +996 XXX XXX XXX.')


class School(models.Model):
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.city} - {self.name}'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('school_admin', 'School Admin'),
        ('super_admin', 'Super Admin'),
    ]

    phone_number = models.CharField(max_length=15, unique=True)
    name = models.CharField(max_length=255)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    class_number = models.CharField(max_length=255, blank=True, null=True)
    class_letter = models.CharField(max_length=255, blank=True, null=True)
    role = models.CharField(max_length=100, choices=ROLE_CHOICES, default='student')

    def __str__(self):
        return f'{self.name} ({self.phone_number}) - {self.school}'
