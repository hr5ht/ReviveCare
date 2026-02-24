# patient/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from twilio.rest import Client
from django.utils import timezone
import json
import logging
import os
import re
from datetime import datetime, date, timedelta
from .models import Patient, SLS
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from a .env file
load_dotenv()  

# Import LangChain components
try:
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("Warning: langchain not installed. Chatbot will use mock responses.")

# Configuration
# by default, it loads from a file named ".env" in the current directory

# GROQ_API_KEY and EMAIL_PASSWORD come from .env
os.environ.setdefault("SMTP_SERVER", "smtp.gmail.com")
os.environ.setdefault("SMTP_PORT", "587")
os.environ.setdefault("EMAIL_SENDER", "actualharshit@gmail.com")
os.environ.setdefault("DOCTOR_EMAIL", "harshitxgarg@gmail.com")
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
            
            patient_response = parsed.get("patient_response", "")
            seriousness_score = float(parsed.get("seriousness_score", 0.0))
            
            # Clamp seriousness score between 0 and 1
            seriousness_score = max(0.0, min(1.0, seriousness_score))
            
            return patient_response, seriousness_score
        else:
            return "I apologize, but I'm having trouble processing your request. Please try rephrasing your question.", 0.0
            
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        print(f"Parsing error: {e}")
        return "I apologize, but I'm having trouble processing your request. Please try rephrasing your question.", 0.0


def send_email_alert(patient, user_query, patient_response, seriousness_score):
    """Email the doctor when a chat message scores as serious. Returns True if it was sent."""
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
    try:
        send_mail(f"URGENT - Patient Alert: {patient.name} (Score: {seriousness_score:.2f})",
                  body, None, [os.getenv('DOCTOR_EMAIL', 'harshitxgarg@gmail.com')])
        return True
    except Exception:
        logger.exception('Doctor alert email for patient %s failed', patient.id)
        return False


MODEL_UNAVAILABLE = ("I'm having trouble answering right now. Please try again in a few minutes. "
                     "If this is urgent, contact your doctor or hospital directly.")
CHAT_RATE_LIMIT = 20  # messages per patient
CHAT_RATE_WINDOW = 10 * 60  # seconds


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
        
        # Get or initialize chat history
        chat_history = request.session.get('chat_history', [])
        
        # Prepare system prompt with patient context
        system_prompt = SYSTEM_PROMPT.format(patient_context=patient.info)
        
        if LANGCHAIN_AVAILABLE:
            # Use real AI model
            llm = initialize_model()
            
            # Build messages
            messages = [SystemMessage(content=system_prompt)]
            
            # Add conversation history
            for msg in chat_history:
                if msg['role'] == 'user':
                    messages.append(HumanMessage(content=msg['content']))
                else:
                    messages.append(AIMessage(content=msg['content']))
            
            # Add current query
            messages.append(HumanMessage(content=user_message))
            
            # Get AI response
            try:
                response = llm.invoke(messages)
            except Exception:
                logger.exception('Chatbot model call failed')
                return JsonResponse({'success': False, 'error': MODEL_UNAVAILABLE}, status=503)
            patient_response, seriousness_score = parse_response(response)
            
        else:
            # Mock response for development
            patient_response = f"I understand your concern about: '{user_message}'. Based on your recovery plan, this seems normal. However, I'm currently in development mode. Please consult your doctor for specific medical advice."
            seriousness_score = 0.2
        
        # Update chat history
        chat_history.append({'role': 'user', 'content': user_message})
        chat_history.append({'role': 'assistant', 'content': patient_response})
        
        # Keep only last 20 messages to prevent session bloat
        if len(chat_history) > 20:
            chat_history = chat_history[-20:]
        
        request.session['chat_history'] = chat_history
        request.session.modified = True
        
        # Send email alert if high seriousness
        if seriousness_score > 0.75:
            send_email_alert(patient, user_message, patient_response, seriousness_score)
        
        return JsonResponse({
            'success': True,
            'response': patient_response,
            'seriousness_score': seriousness_score
        })
        
    except Patient.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Patient not found'})
    except Exception:
        logger.exception('chatbot_send failed')
        return JsonResponse({'success': False, 'error': MODEL_UNAVAILABLE}, status=500)
