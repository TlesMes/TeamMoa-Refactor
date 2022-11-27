from django.db import models

# Create your models here.


class WeekSchedule(models.Model):
    dayschedule = models.ForeignKey('schedules.DaySchedule', related_name="week", on_delete=models.CASCADE)
    

#팀에 시간대별로 몇명이 가용시간인지
class TeamDaySchedule(models.Model):
    date = models.DateField()

    time_0 = models.PositiveIntegerField()
    time_1 = models.PositiveIntegerField()
    time_2 = models.PositiveIntegerField()
    time_3 = models.PositiveIntegerField()
    time_4 = models.PositiveIntegerField()
    time_5 = models.PositiveIntegerField()
    time_6 = models.PositiveIntegerField()
    time_7 = models.PositiveIntegerField()
    time_8 = models.PositiveIntegerField()
    time_9 = models.PositiveIntegerField()
    time_10 = models.PositiveIntegerField()
    time_11 = models.PositiveIntegerField()
    time_12 = models.PositiveIntegerField()
    time_13 = models.PositiveIntegerField()
    time_14 = models.PositiveIntegerField()
    time_15 = models.PositiveIntegerField()
    time_16 = models.PositiveIntegerField()
    time_17 = models.PositiveIntegerField()
    time_18 = models.PositiveIntegerField()
    time_19 = models.PositiveIntegerField()
    time_20 = models.PositiveIntegerField()
    time_21 = models.PositiveIntegerField()
    time_22 = models.PositiveIntegerField()
    time_23 = models.PositiveIntegerField()

#개인별로 가능한 시간대가 언제인지
class PersonalDaySchedule(models.Model):
    dayoftheweek_choices=(
        (1,'일'),
        (2,'월'),
        (3,'화'),
        (4,'수'),
        (5,'목'),
        (6,'금'),
        (7,'토'),
    )
    #해당 day스케줄이 어느 요일인지 (날짜로 바꿀수도?)
    dayoftheweek = models.PositiveIntegerField(choices=dayoftheweek_choices)

    #시간대별 가능 여부를 저장한 bool필드
    time_0 = models.BooleanField(default=False)
    time_1 = models.BooleanField(default=False)
    time_2 = models.BooleanField(default=False)
    time_3 = models.BooleanField(default=False)
    time_4 = models.BooleanField(default=False)
    time_5 = models.BooleanField(default=False)
    time_6 = models.BooleanField(default=False)
    time_7 = models.BooleanField(default=False)
    time_8 = models.BooleanField(default=False)
    time_9 = models.BooleanField(default=False)
    time_10 = models.BooleanField(default=False)
    time_11 = models.BooleanField(default=False)
    time_12 = models.BooleanField(default=False)
    time_13 = models.BooleanField(default=False)
    time_14 = models.BooleanField(default=False)
    time_15 = models.BooleanField(default=False)
    time_16 = models.BooleanField(default=False)
    time_17 = models.BooleanField(default=False)
    time_18 = models.BooleanField(default=False)
    time_19 = models.BooleanField(default=False)
    time_20 = models.BooleanField(default=False)
    time_21 = models.BooleanField(default=False)
    time_22 = models.BooleanField(default=False)
    time_23 = models.BooleanField(default=False)


