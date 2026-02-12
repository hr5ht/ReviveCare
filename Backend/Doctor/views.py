from django.shortcuts import render
import json
from django.http import JsonResponse
from Patients.models import Patient
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

# Create your views here.



@require_POST
def doctor_info(request):
    data = json.loads(request.body)

    patient, created = Patient.objects.update_or_create(
        email=data['email'],          # lookup (UNIQUE)
        defaults={
            'name': data['name'],
            'info': data['info'],
        }
    )

    return JsonResponse({
        'success': True,
        'created': created,   # true = new, false = updated
    })
