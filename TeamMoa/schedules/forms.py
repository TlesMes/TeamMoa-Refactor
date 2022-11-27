from schedules.models import DaySchedule
from django import forms
#닉네임, 
class CreateTeamForm(forms.ModelForm):
    class Meta:
        model = DaySchedule
        fields = [
            'time_0',
            'time_1',
            'time_2',
            'time_3',
            'time_4',
            'time_5',
            'time_6',
            'time_7',
            'time_8',
            'time_9',
            'time_10',
            'time_11',
            'time_12',
            'time_13',
            'time_14',
            'time_15',
            'time_16',
            'time_17',
            'time_18',
            'time_19',
            'time_20',
            'time_21',
            'time_22',
            'time_23',
        ]