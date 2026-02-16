from django.contrib.auth.hashers import identify_hasher, make_password
from django.db import migrations


def hash_plain_passwords(apps, schema_editor):
    Patient = apps.get_model('Patients', 'Patient')
    for patient in Patient.objects.all():
        try:
            identify_hasher(patient.password)  # already hashed
        except ValueError:
            patient.password = make_password(patient.password)
            patient.save(update_fields=['password'])


class Migration(migrations.Migration):

    dependencies = [
        ('Patients', '0009_armraise_jumpingjack'),
    ]

    operations = [
        migrations.RunPython(hash_plain_passwords, migrations.RunPython.noop),
    ]
