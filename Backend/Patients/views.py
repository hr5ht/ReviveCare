# Patients/views.py — chatbot endpoint and doctor alert email
# Env (loaded by settings): GROQ_API_KEY, GROQ_MODEL, DOCTOR_EMAIL; optional SMS: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN,
# TWILIO_PHONE_NUMBER, TO_NUMBER (fallback when the doctor's profile has no phone); email settings live in settings.py
import json
import logging
import os
import re
import threading
from datetime import timedelta
from types import SimpleNamespace

from django.core.cache import cache
from django.core.mail import send_mail
from django.http import JsonResponse, StreamingHttpResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from Doctor.models import DoctorProfile
from Home.views import conversation, days_in_recovery, exercise_streak, goal_cards, weekly_summary

from .models import Alert, ChatMessage, Patient

logger = logging.getLogger(__name__)

try:
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger.warning('langchain not installed; chatbot will use mock responses')
SYSTEM_PROMPT = """IT IS JUST FOR EDUCATIONAL PURPOSES ONLY.You are ReViveCare, an AI-powered post-discharge recovery support chatbot.
Your role is to support patients emotionally and informationally during recovery after surgery or injury.
You are NOT a doctor and you MUST NOT diagnose, prescribe medication, or alter treatment plans.

You will be given full patient context provided by their doctor.
Use this context to answer user queries accurately, calmly, and empathetically.

Your goals:
1. Reassure and guide the patient using simple, non-alarming language
2. Compare their reported symptoms against their specific medical context
3. Determine if symptoms align with expected recovery for THEIR condition
4. Encourage appropriate next steps without diagnosing
5. Detect potentially serious situations based on THEIR specific medical context

IMPORTANT RULES:
- Never provide a diagnosis
- Never prescribe or change medications
- Never claim certainty about outcomes
- Never dismiss the user's concern
- Be calm, supportive, and empathetic
- Base all assessments on the patient's specific condition and context provided by their doctor

You must return EXACTLY a valid JSON object for every user message with these keys:
1. patient_response: A clear, supportive answer to the user's query based on their specific medical context.
   Write it as plain text for a chat bubble: no Markdown (no asterisks, #, tables or bullet symbols).
   Keep it short and use line breaks between separate points.
2. seriousness_score: A single floating-point number between 0.0 and 1.0

SERIOUSNESS SCORING GUIDELINES:
0.00 – 0.30 → Symptoms align with expected recovery for their specific condition, reassurance sufficient
0.31 – 0.60 → Monitor closely, routine follow-up advised based on their condition
0.61 – 0.75 → Concerning for their specific condition, recommend contacting doctor soon
> 0.75 → Potential red flag for their specific condition, immediate escalation required

When scoring seriousness:
- Consider the patient's specific condition and what is normal for THEIR recovery
- Compare symptoms against expected vs. concerning signs for THEIR medical context
- Account for their prescribed medications and potential side effects
- Consider their recovery timeline and stage

If seriousness_score > 0.75:
- In your patient_response, calmly advise the patient to contact their doctor or hospital immediately
- Do NOT use panic-inducing language unless absolutely necessary
- Reference their specific condition when explaining why they should seek help

STRICT OUTPUT FORMAT (valid JSON only, no extra text):
{{
  "patient_response": "your response here",
  "seriousness_score": 0.0
}}

PATIENT MEDICAL CONTEXT:
{patient_context}
"""


def patient_context(patient):
    """The doctor's notes plus the patient's current plan and recent workout progress, for the system prompt."""
    week = weekly_summary(patient)
    lines = [patient.info, '']
    if patient.condition:
        lines.append(f"Condition: {patient.condition}")
    if patient.surgery_date:
        lines.append(f"Surgery/discharge date: {patient.surgery_date:%d %b %Y} ({days_in_recovery(patient)} days ago)")
    plan = [f"{p.exercise.name} {p.total_sets} x {p.reps}" for p in patient.plan.filter(is_active=True).select_related('exercise')]
    lines.append(f"Exercise plan: {', '.join(plan) or 'none assigned'}")
    lines.append(f"Last 7 days: {week['reps']} reps on {week['active_days']} days"
                 + (f", average form quality {week['quality']}%" if week['quality'] is not None else '')
                 + f". Current streak: {exercise_streak(patient)} days.")
    diary = patient.diary.filter(created_at__gte=timezone.now() - timedelta(days=7))[:10]
    if diary:
        lines.append("Pain diary, last 7 days (newest first, pain 0-10):")
        for e in diary:
            extra = ', '.join(e.symptom_labels() + ([f'note: "{e.notes}"'] if e.notes else []))
            lines.append(f"- {timezone.localtime(e.created_at):%a %d %b %H:%M}: pain {e.pain}"
                         + (f" ({e.get_context_display().lower()})" if e.context != 'diary' else '') + (f"; {extra}" if extra else ''))
    goals = [f"{g['text']} ({'done' if g['achieved'] else str(g['percent']) + '%'})" for g in goal_cards(patient)]
    if goals:
        lines.append(f"Recovery goals: {'; '.join(goals)}")
    return '\n'.join(lines)


# ============================================================================
# PATIENT AUTHENTICATION & DASHBOARD VIEWS
# ============================================================================






# ============================================================================
# CHATBOT VIEWS
# ============================================================================



def initialize_model():
    """Initialize the ChatGroq model"""
    if not LANGCHAIN_AVAILABLE:
        return None
    return ChatGroq(
        model=os.getenv('GROQ_MODEL', 'openai/gpt-oss-120b'),  # override when Groq retires a model
        temperature=0.3,
        max_tokens=1024,
        timeout=30,
        max_retries=2,
    )


def parse_response(raw_response):
    """Parse AI response to extract patient_response and seriousness_score"""
    try:
        response_text = raw_response.content.strip()
        
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            json_str = json_match.group(0)
            parsed = json.loads(json_str)
            
            patient_response = _line_breaks(parsed.get("patient_response", ""))
            seriousness_score = float(parsed.get("seriousness_score", 0.0))
            
            # Clamp seriousness score between 0 and 1
            seriousness_score = max(0.0, min(1.0, seriousness_score))
            
            return patient_response, seriousness_score
        else:
            return "I apologize, but I'm having trouble processing your request. Please try rephrasing your question.", 0.0
            
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.warning("Could not parse chatbot response: %s", e)
        return "I apologize, but I'm having trouble processing your request. Please try rephrasing your question.", 0.0


def _line_breaks(text):
    """Models sometimes double-escape newlines in their JSON, which would show up as a literal \\n in the chat bubble."""
    return text.replace('\\n', '\n')


_REPLY_START = re.compile(r'"patient_response"\s*:\s*"')


def partial_reply(raw):
    """The patient_response text decoded so far from a JSON reply that is still being generated."""
    m = _REPLY_START.search(raw)
    if not m:
        return ''
    text, escaped = raw[m.end():], False
    for i, ch in enumerate(text):
        if escaped:
            escaped = False
        elif ch == '\\':
            escaped = True
        elif ch == '"':
            text = text[:i]
            break
    for cut in range(6):  # a half-received escape (\ or \u00e) can't decode yet; trim it off
        try:
            return _line_breaks(json.loads(f'"{text[:len(text) - cut]}"', strict=False)).rstrip('\\')
        except ValueError:
            pass
    return ''


def _send_quietly(subject, body, to, sms_to, patient_id):
    try:
        send_mail(subject, body, None, [to])
    except Exception:
        logger.exception('Doctor alert email for patient %s failed', patient_id)
    if sms_to:
        try:
            from twilio.rest import Client
            Client(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN']).messages.create(
                to=sms_to, from_=os.environ['TWILIO_PHONE_NUMBER'], body=f"ReViveCare: {subject}. Check your alerts.")
        except Exception:
            logger.exception('Doctor alert SMS for patient %s failed', patient_id)


def _doctor_phone(patient):
    """Where to text alerts: the doctor's profile phone, else TO_NUMBER; None when Twilio isn't configured."""
    if not all(os.getenv(k) for k in ('TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_PHONE_NUMBER')):
        return None
    profile = patient.doctor and DoctorProfile.objects.filter(user=patient.doctor).first()
    return (profile and profile.phone) or os.getenv('TO_NUMBER') or None


def send_email_alert(patient, user_query, patient_response, seriousness_score):
    """Email (and text, if Twilio is set up) the patient's doctor about a serious chat message, without making the patient wait.

    Everything that touches the database happens here; the thread only talks to SMTP. The Alert row is the record if mail fails.
    """
    to = (patient.doctor and patient.doctor.email) or os.getenv('DOCTOR_EMAIL', 'harshitxgarg@gmail.com')
    body = f"""URGENT PATIENT ALERT - ReViveCare
============================================

Alert Time: {timezone.localtime():%Y-%m-%d %H:%M} IST
Patient Name: {patient.name}
Patient Email: {patient.email}
Seriousness Score: {seriousness_score:.2f}

LATEST PATIENT QUERY:
{user_query}

SYSTEM RESPONSE TO PATIENT:
{patient_response}

PATIENT MEDICAL CONTEXT:
{patient.info}

RECOMMENDATION:
Please contact the patient immediately to assess their condition and provide appropriate medical guidance.

This is an automated alert from the ReViveCare post-discharge monitoring system.
"""
    subject = f"URGENT - Patient Alert: {patient.name} (Score: {seriousness_score:.2f})"
    # ponytail: plain thread; a serverless instance may freeze it after the response, move to a task queue if mails go missing
    threading.Thread(target=_send_quietly, args=(subject, body, to, _doctor_phone(patient), patient.id), daemon=True).start()


MODEL_UNAVAILABLE = ("I'm having trouble answering right now. Please try again in a few minutes. "
                     "If this is urgent, contact your doctor or hospital directly.")
ALERT_THRESHOLD = 0.75  # seriousness above this goes to the doctor's alerts
CHAT_CONTEXT_MESSAGES = 20
CHAT_LANGUAGES = {'english': 'English', 'hindi': 'Hindi', 'marathi': 'Marathi', 'tamil': 'Tamil'}
CHAT_RATE_LIMIT = 20  # messages per patient
CHAT_RATE_WINDOW = 10 * 60  # seconds


@require_http_methods(["POST"])
def chatbot_new(request):
    if not Patient.objects.filter(id=request.session.get('patient_id')).update(chat_since=timezone.now()):
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    return JsonResponse({'success': True})


def _save_turn(patient, user_message, reply, score):
    """Store both messages (and an alert if serious); returns the reply's id for feedback."""
    ChatMessage.objects.create(patient=patient, role='user', content=user_message)
    saved = ChatMessage.objects.create(patient=patient, role='assistant', content=reply, seriousness=score)
    if score > ALERT_THRESHOLD:
        Alert.objects.create(patient=patient, message=user_message, response=reply, seriousness=score)
        send_email_alert(patient, user_message, reply, score)
    return saved.id


@require_http_methods(["POST"])
def chatbot_feedback(request):
    """Thumbs up/down on a reply: {"id": message id, "helpful": true/false/null}."""
    data = json.loads(request.body or '{}')
    helpful = data.get('helpful')
    updated = ChatMessage.objects.filter(id=data.get('id'), role='assistant', patient_id=request.session.get('patient_id')) \
        .update(helpful=helpful if helpful in (True, False) else None)
    return JsonResponse({'success': bool(updated)}, status=200 if updated else 404)


def _stream_reply(model, messages, patient, user_message):
    """NDJSON lines: {"delta": text} while the reply generates, then {"done": true, "response", "seriousness_score"}."""
    raw, sent = '', ''
    try:
        for chunk in model.stream(messages):
            raw += chunk.content
            text = partial_reply(raw)
            if len(text) > len(sent):
                yield json.dumps({'delta': text[len(sent):]}) + '\n'
                sent = text
    except Exception:
        logger.exception('Chatbot model stream failed')
        yield json.dumps({'error': MODEL_UNAVAILABLE}) + '\n'
        return
    reply, score = parse_response(SimpleNamespace(content=raw))
    message_id = _save_turn(patient, user_message, reply, score)
    yield json.dumps({'done': True, 'id': message_id, 'response': reply, 'seriousness_score': score}) + '\n'


@require_http_methods(["POST"])
def chatbot_send(request):
    """Handle chatbot message sending"""
    patient_id = request.session.get('patient_id')
    if not patient_id:
        return JsonResponse({'success': False, 'error': 'Not authenticated'})

    # ponytail: per-instance memory cache; move to a shared cache if the limit must hold across instances
    rate_key = f'chatbot-messages:{patient_id}'
    cache.add(rate_key, 0, CHAT_RATE_WINDOW)
    if cache.incr(rate_key) > CHAT_RATE_LIMIT:
        return JsonResponse({'success': False, 'error': 'You are sending messages too quickly. Please wait a few minutes.'}, status=429)
    
    try:
        # Get patient
        patient = Patient.objects.get(id=patient_id)
        
        # Parse request
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'success': False, 'error': 'Empty message'})
        
        # The model sees the last CHAT_CONTEXT_MESSAGES turns of the stored conversation
        chat_history = list(conversation(patient).order_by('-created_at', '-id')[:CHAT_CONTEXT_MESSAGES])[::-1]
        
        # Prepare system prompt with patient context
        system_prompt = SYSTEM_PROMPT.format(patient_context=patient_context(patient))
        language = CHAT_LANGUAGES.get(data.get('language'), 'English')
        if language != 'English':
            system_prompt += f"\nWrite patient_response in {language}, in simple everyday words. Keep the JSON keys in English.\n"
        
        if LANGCHAIN_AVAILABLE:
            # Build messages
            messages = [SystemMessage(content=system_prompt)]
            
            # Add conversation history
            for msg in chat_history:
                messages.append((HumanMessage if msg.role == 'user' else AIMessage)(content=msg.content))
            
            # Add current query
            messages.append(HumanMessage(content=user_message))
            
            # Get AI response (model creation is inside the try: a missing API key fails here too)
            try:
                model = initialize_model()
                if data.get('stream'):
                    return StreamingHttpResponse(_stream_reply(model, messages, patient, user_message), content_type='application/x-ndjson')
                response = model.invoke(messages)
            except Exception:
                logger.exception('Chatbot model call failed')
                return JsonResponse({'success': False, 'error': MODEL_UNAVAILABLE}, status=503)
            patient_response, seriousness_score = parse_response(response)
            
        else:
            # Mock response for development
            patient_response = f"I understand your concern about: '{user_message}'. Based on your recovery plan, this seems normal. However, I'm currently in development mode. Please consult your doctor for specific medical advice."
            seriousness_score = 0.2
        
        message_id = _save_turn(patient, user_message, patient_response, seriousness_score)
        return JsonResponse({
            'success': True,
            'id': message_id,
            'response': patient_response,
            'seriousness_score': seriousness_score
        })
        
    except Patient.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Patient not found'})
    except Exception:
        logger.exception('chatbot_send failed')
        return JsonResponse({'success': False, 'error': MODEL_UNAVAILABLE}, status=500)
