from django.contrib import admin
from .models import Subject, Test, Question, AnswerOption, Event, Answer, Result, Recommendation

admin.site.register(Subject)
admin.site.register(Test)
admin.site.register(Question)
admin.site.register(AnswerOption)
admin.site.register(Event)
admin.site.register(Answer)
admin.site.register(Result)
admin.site.register(Recommendation)
