import datetime

from django import forms
from django.utils import timezone

from Patients.models import Exercise, Medication, Patient, RecoveryGoal


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


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['name', 'email', 'condition', 'surgery_date', 'phone', 'emergency_contact_name', 'emergency_contact_phone', 'info']
        labels = {'info': 'Patient information', 'surgery_date': 'Surgery / discharge date'}

    def clean_surgery_date(self):
        date = self.cleaned_data['surgery_date']
        if date and date > timezone.localdate():
            raise forms.ValidationError('The surgery date is in the future.')
        return date


class MedicationForm(forms.ModelForm):
    times = forms.CharField(label='Times each day', help_text='24-hour times, comma separated, e.g. 08:00, 20:00')

    class Meta:
        model = Medication
        fields = ['name', 'dose', 'times', 'instructions', 'start_date', 'end_date']
        labels = {'dose': 'Dose', 'instructions': 'Instructions', 'start_date': 'Start', 'end_date': 'End (optional)'}

    def clean_times(self):
        times = []
        for part in self.cleaned_data['times'].replace(';', ',').split(','):
            try:
                times.append(datetime.datetime.strptime(part.strip(), '%H:%M').strftime('%H:%M'))
            except ValueError:
                raise forms.ValidationError(f'"{part.strip()}" is not a time like 08:00.')
        if len(times) > 6:
            raise forms.ValidationError('At most 6 doses a day.')
        return sorted(set(times))

    def clean(self):
        data = super().clean()
        if data.get('end_date') and data.get('start_date') and data['end_date'] < data['start_date']:
            self.add_error('end_date', 'The end date is before the start date.')
        return data
