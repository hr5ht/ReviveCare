import datetime

from django import forms
from django.utils import timezone

from Patients.models import Exercise, RecoveryGoal


class DoctorProfileForm(forms.Form):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    specialty = forms.CharField(max_length=100, required=False)
    phone = forms.RegexField(regex=r'^\+?[0-9 ()-]{7,20}$', max_length=20, required=False,
                             error_messages={'invalid': 'Enter a valid phone number.'})


class RecoveryGoalForm(forms.Form):
    kind = forms.ChoiceField(choices=RecoveryGoal.KINDS)
    target = forms.IntegerField(min_value=1, max_value=10000)
    exercise = forms.ModelChoiceField(queryset=Exercise.objects.filter(is_active=True), required=False, empty_label='Any exercise')
    due_date = forms.DateField(required=False)

    def clean(self):
        data = super().clean()
        if data.get('kind') == 'range' and not data.get('exercise'):
            self.add_error('exercise', 'Pick the exercise this angle applies to.')
        if data.get('kind') == 'range' and data.get('target', 0) > 180:
            self.add_error('target', 'Angles go up to 180°.')
        due = data.get('due_date')
        if due and due < timezone.localdate():
            self.add_error('due_date', 'The due date is in the past.')
        return data
