from django.contrib.auth.models import User
from django.db import models
from django.db.models import Avg
from register.models import School


class Subject(models.Model):
    name = models.CharField(max_length=300)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name = 'Предметы'
        verbose_name_plural = 'Предметы'


class Test(models.Model):
    name = models.CharField(max_length=500)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    description = models.TextField()
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='tests')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tests')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} - {self.subject} {self.school} {self.created_by.profile.role}'

    class Meta:
        verbose_name = 'Тесты'
        verbose_name_plural = 'Тесты'


class Question(models.Model):
    text = models.TextField('Текст вопроса')
    image = models.ImageField('Изображения вопроса', upload_to='question/img/', blank=True, null=True)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    number = models.PositiveIntegerField('Номер вопроса', blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.number is None:
            max_number = Question.objects.filter(test=self.test).aggregate(models.Max('number')).get('number__max')
            self.number = (max_number or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Вопрос {self.number}: {self.text[:30]}'

    class Meta:
        verbose_name = 'Вопросы'
        verbose_name_plural = 'Вопросы'


class AnswerOption(models.Model):
    question = models.ForeignKey(Question, related_name="options", on_delete=models.CASCADE)
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField()

    @property
    def letter(self):
        letters = ['А', 'Б', 'В', 'Г', 'Д', 'Е']
        index = list(self.question.options.all()).index(self) if self in self.question.options.all() else None
        return letters[index] if index is not None and index < len(letters) else '?'

    def __str__(self):
        return f'{self.letter}. {self.text} ({self.is_correct})'

    class Meta:
        verbose_name = 'Вариант ответа'
        verbose_name_plural = 'Вариант ответа'


class Event(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='event')
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.test.name} - {self.school} on {self.date}/{self.time}"

    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'Событие'


class Answer(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(AnswerOption, on_delete=models.CASCADE)
    is_correct = models.BooleanField()

    def __str__(self):
        return f"Answer by {self.student.profile.name} for {self.question.text[:30]}"

    class Meta:
        verbose_name = 'Прохождение'
        verbose_name_plural = 'Прохождение'


class Result(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Ученик")
    test = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name="Тест")
    percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Процент")
    mistakes = models.ManyToManyField(Question, blank=True, related_name="mistakes", verbose_name="Ошибки")
    date_taken = models.DateTimeField(auto_now_add=True, verbose_name="Дата прохождения")
    total_questions_count = models.PositiveIntegerField(default=0, blank=True, null=True, verbose_name="Всего вопросов")
    correct_answers_count = models.PositiveIntegerField(default=0, blank=True, null=True,
                                                        verbose_name="Правильные ответы")
    not_correct_answers_count = models.PositiveIntegerField(default=0, blank=True, null=True,
                                                            verbose_name="Неправильные ответы")

    def __str__(self):
        return f"{self.student.username} - {self.test.name} - {self.percentage}%"

    class Meta:
        verbose_name = 'Результат'
        verbose_name_plural = 'Результат'


class Recommendation(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, verbose_name="Школа")
    class_number = models.CharField(max_length=50, verbose_name="Класс", help_text="Например: 11")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Предмет")
    min_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="Минимальный процент",
        help_text="Минимальный результат, например: 40"
    )
    max_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="Максимальный процент",
        help_text="Максимальный результат, например: 60"
    )
    message = models.TextField(verbose_name="Сообщение", help_text="Текст сообщения для отправки")
    link = models.URLField(blank=True, null=True, verbose_name="Ссылка", help_text="Ссылка для учеников")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"Recommendation for {self.subject.name} - Class {self.class_number}"

    class Meta:
        verbose_name = 'Рекомендации'
        verbose_name_plural = 'Рекомендации'


class TestHistory(models.Model):
    student = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Ученик")
    full_name = models.CharField(max_length=255, blank=True, verbose_name="ФИО")
    results = models.ManyToManyField(Result, related_name="test_history", verbose_name="Результаты", blank=True)
    average_percentage = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.full_name}"

    class Meta:
        verbose_name = "История тестов"
        verbose_name_plural = "История тестов"


class SchoolHistory(models.Model):
    school = models.OneToOneField(School, on_delete=models.CASCADE, verbose_name="Школа")
    total_students = models.PositiveIntegerField(default=0, verbose_name="Количество учеников")
    average_percentage = models.FloatField(default=0.0)
    results = models.ManyToManyField(Result, related_name="school_histories")

    def __str__(self):
        return f"{self.school}"

    class Meta:
        verbose_name = "История школы"
        verbose_name_plural = "История школ"
