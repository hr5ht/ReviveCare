from django import forms

from Patients.models import DiaryEntry

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
