from django import forms


class DoctorProfileForm(forms.Form):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    specialty = forms.CharField(max_length=100, required=False)
    phone = forms.RegexField(regex=r'^\+?[0-9 ()-]{7,20}$', max_length=20, required=False,
                             error_messages={'invalid': 'Enter a valid phone number.'})
