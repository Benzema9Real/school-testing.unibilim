from django.contrib.auth.models import User
from django.db import models
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
    image = models.ImageField('Изображения вопроса', upload_to='question/img/',blank=True, null=True )
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')

    def __str__(self):
        return f'{self.test} {self.text} {self.image}'

    class Meta:
        verbose_name = 'Вопросы'
        verbose_name_plural = 'Вопросы'


class AnswerOption(models.Model):
    question = models.ForeignKey(Question, related_name="options", on_delete=models.CASCADE)
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField()

    def __str__(self):
        return f'{self.question} {self.text} {self.is_correct}'

    class Meta:
        verbose_name = 'Варианты ответа'
        verbose_name_plural = 'Варианты ответа'


class Event(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='event')
    date = models.DateField()
    time = models.TimeField()

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
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    mistakes = models.ManyToManyField(Question, blank=True, related_name="mistakes")
    date_taken = models.DateTimeField(auto_now_add=True)

    def total_questions(self):
        return self.test.questions.count()

    def correct_answers(self):
        return self.total_questions() - self.mistakes.count()

    def __str__(self):
        return f"{self.student.username} - {self.test.name} - {self.percentage}%"

    class Meta:
        verbose_name = 'Результат'
        verbose_name_plural = 'Результат'


class Recommendation(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    condition = models.CharField(max_length=255, help_text="Например: <60")
    content = models.TextField()
    link = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Recommendation for {self.subject.name}"

    class Meta:
        verbose_name = 'Рекомендации'
        verbose_name_plural = 'Рекомендации'
