from django import forms

PHONE = dict(regex=r'^\+?[0-9 ()-]{7,20}$', max_length=20, required=False,
             error_messages={'invalid': 'Enter a valid phone number.'})


class PatientContactForm(forms.Form):
    phone = forms.RegexField(label='Your phone', **PHONE)
    emergency_contact_name = forms.CharField(label='Emergency contact name', max_length=100, required=False)
    emergency_contact_phone = forms.RegexField(label='Emergency contact phone', **PHONE)
