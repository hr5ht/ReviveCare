# patient/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from twilio.rest import Client
from django.utils import timezone
import json
import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date, timedelta
from .models import Patient, SLS
import os
from dotenv import load_dotenv

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
1. patient_response: A clear, supportive answer to the user's query based on their specific medical context
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
        model="llama-3.3-70b-versatile",
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
    """Send email alert to doctor when seriousness score is high"""
    try:
        smtp_server = os.environ.get("SMTP_SERVER")
        smtp_port = int(os.environ.get("SMTP_PORT"))
        sender_email = os.environ.get("EMAIL_SENDER")
        sender_password = os.environ.get("EMAIL_PASSWORD")
        doctor_email = os.environ.get("DOCTOR_EMAIL")
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = doctor_email
        msg['Subject'] = f"🚨 URGENT - Patient Alert: {patient.name} (Score: {seriousness_score:.2f})"
        
        email_body = f"""
URGENT PATIENT ALERT - ReViveCare System
============================================

Alert Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
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
        
        msg.attach(MIMEText(email_body, 'plain'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, doctor_email, text)
        server.quit()
        
        '''print(f"✅ EMAIL ALERT SENT TO DOCTOR: {doctor_email}")
        TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
        TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
        TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")  # Your Twilio phone number
        TO_NUMBER = os.getenv("TO_NUMBER")
            
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            
        call = client.calls.create(
            to=TO_NUMBER,
            from_=TWILIO_PHONE_NUMBER,
            twiml=f"<Response><Say voice='alice'>This is an emergency please call {patient.name}</Say></Response>"
        )
            
        context = {
            'call_sid': call.sid,
            'status': 'Call initiated successfully',
            'phone_number': TO_NUMBER,
            'message': f"IVR call is being made to say  'This is an emergency please call {patient.name}'"
        }'''
        
    except Exception as e:
        print(f"⚠️ EMAIL SEND FAILED: {str(e)}")
        context = {
            'status': 'Error making call',
            'error': str(e)
        }

@csrf_exempt
@require_http_methods(["POST"])
def chatbot_send(request):
    """Handle chatbot message sending"""
    print(f"DEBUG: Session ID: {request.session.session_key}")
    print(f"DEBUG: User in session: {request.session.get('patient_id')}")
    
    patient_id = request.session.get('patient_id')
    if not patient_id:
        return JsonResponse({'success': False, 'error': 'Not authenticated'})
    
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
            response = llm.invoke(messages)
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
    except Exception as e:
        print(f"Error in chatbot_send: {e}")
        return JsonResponse({'success': False, 'error': 'Server error'})
