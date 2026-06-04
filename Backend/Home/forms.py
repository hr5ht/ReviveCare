from django import forms
from django.utils.translation import gettext_lazy as _

from Patients.models import DiaryEntry, Vitals

from .models import DemoRequest

PHONE = dict(regex=r'^\+?[0-9 ()-]{7,20}$', max_length=20, required=False,
             error_messages={'invalid': 'Enter a valid phone number.'})


class PatientContactForm(forms.Form):
    phone = forms.RegexField(label='Your phone', **PHONE)
    emergency_contact_name = forms.CharField(label='Emergency contact name', max_length=100, required=False)
    emergency_contact_phone = forms.RegexField(label='Emergency contact phone', **PHONE)


class DiaryForm(forms.Form):
    pain = forms.IntegerField(min_value=0, max_value=10)
    symptoms = forms.MultipleChoiceField(choices=DiaryEntry.SYMPTOMS, required=False)
    notes = forms.CharField(max_length=1000, required=False)


class VitalsForm(forms.ModelForm):
    class Meta:
        model = Vitals
        fields = ['systolic', 'diastolic', 'heart_rate', 'temperature']
        labels = {'systolic': _('Blood pressure (top number)'), 'diastolic': _('Blood pressure (bottom number)'),
                  'heart_rate': _('Heart rate (beats per minute)'), 'temperature': _('Temperature (°F)')}

    def clean(self):
        data = super().clean()
        if not any(data.get(f) is not None for f in self.Meta.fields):
            raise forms.ValidationError(_('Enter at least one reading.'))
        if (data.get('systolic') is None) != (data.get('diastolic') is None):
            raise forms.ValidationError(_('Enter both blood pressure numbers, e.g. 120 and 80.'))
        if data.get('systolic') and data.get('diastolic') and data['diastolic'] >= data['systolic']:
            raise forms.ValidationError('The top blood pressure number should be bigger than the bottom one.')
        return data


class DemoRequestForm(forms.ModelForm):
    phone = forms.RegexField(**PHONE)

    class Meta:
        model = DemoRequest
        fields = ['name', 'email', 'organization', 'phone', 'message']
