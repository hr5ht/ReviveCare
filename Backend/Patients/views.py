# patient/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse , StreamingHttpResponse
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
import cv2
import mediapipe as mp
import numpy as np
import threading
import time
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

# Set the API key from the environment, if not already set
os.environ.setdefault("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
os.environ.setdefault("SMTP_SERVER", "smtp.gmail.com")
os.environ.setdefault("SMTP_PORT", "587")
os.environ.setdefault("EMAIL_SENDER", "actualharshit@gmail.com")
os.environ.setdefault("EMAIL_PASSWORD", "xiad gbiy bmwu uwnm")
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

def login(request):
    """Patient login - email only authentication"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        
        try:
            # Check if patient with this email exists
            patient = Patient.objects.get(email=email)
            
            # Email found - log them in
            request.session['patient_id'] = patient.id
            request.session['patient_email'] = patient.email
            request.session['patient_name'] = patient.name
            
            messages.success(request, f'Welcome back, {patient.name}!')
            return redirect('patient_dashboard')
                
        except Patient.DoesNotExist:
            # Email not found - redirect to home
            messages.error(
                request, 
                'Doctor has not updated this email yet. Please come back later.'
            )
            return redirect('home')
    
    # GET request - show login form
    return render(request, 'login_page.html')


def patient_dashboard(request):
    """Patient dashboard"""
    patient_id = request.session.get('patient_id')
    if not patient_id:
        messages.error(request, 'Please log in to access the patient portal.')
        return redirect('login')
    
    try:
        patient = Patient.objects.get(id=patient_id)
        return render(request, 'patient_dashboard.html', {'patient': patient})
    except Patient.DoesNotExist:
        messages.error(request, 'Session expired. Please log in again.')
        return redirect('login')


def patient_logout(request):
    """Logout patient"""
    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

# ============================================================================
# CHATBOT VIEWS
# ============================================================================

def chatbot(request):
    """Chatbot page"""
    patient_id = request.session.get('patient_id')
    if not patient_id:
        messages.error(request, 'Please log in to access the chatbot.')
        return redirect('login')
    
    try:
        patient = Patient.objects.get(id=patient_id)
        
        # Initialize conversation history in session if not exists
        if 'chat_history' not in request.session:
            request.session['chat_history'] = []
        
        return render(request, 'chatbot.html', {'patient': patient})
    except Patient.DoesNotExist:
        messages.error(request, 'Session expired. Please log in again.')
        return redirect('login')


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

# ============================================================================
# EXERCISE VIEWS
# ============================================================================

def exercise(request):
    return render(request , 'exercise.html')

def ar(request):
    return render(request , 'ar.html')

def bc(request):
    return render(request , 'bc.html')

# Add these imports at the top of your views.py
from django.db.models import Sum, Avg, Count, Max
from datetime import timedelta
from .models import Patient, SLS

# Update the sr view (replace the existing one at line 344):
# Replace your existing sr view (around line 344) with this:

def sr(request):
    """Side Lateral Raise exercise page with progress tracking"""
    from django.db.models import Sum, Max
    from datetime import timedelta
    
    patient_id = request.session.get('patient_id')
    
    context = {
        'is_logged_in': False,
        'patient': None,
        'recent_workouts': [],
        'stats': {
            'total_sessions': 0,
            'total_reps': 0,
            'avg_quality': 0,
            'best_session_reps': 0,
        }
    }
    
    if patient_id:
        try:
            patient = Patient.objects.get(id=patient_id)
            context['is_logged_in'] = True
            context['patient'] = patient
            
            # Check if SLS model exists
            try:
                from .models import SLS
                
                # Get recent workouts (last 7 days)
                seven_days_ago = timezone.now().date() - timedelta(days=7)
                recent_workouts = SLS.objects.filter(
                    patient=patient,
                    date__gte=seven_days_ago
                ).order_by('-created_at')[:5]
                
                context['recent_workouts'] = recent_workouts
                
                # Calculate stats
                all_workouts = SLS.objects.filter(patient=patient)
                
                if all_workouts.exists():
                    context['stats'] = {
                        'total_sessions': all_workouts.count(),
                        'total_reps': all_workouts.aggregate(Sum('total_reps'))['total_reps__sum'] or 0,
                        'avg_quality': round(sum([w.quality_score for w in all_workouts]) / all_workouts.count(), 1) if all_workouts.count() > 0 else 0,
                        'best_session_reps': all_workouts.aggregate(Max('total_reps'))['total_reps__max'] or 0,
                    }
            except ImportError:
                # SLS model doesn't exist yet - migrations not run
                print("SLS model not found. Please run: python manage.py makemigrations && python manage.py migrate")
                pass
                
        except Patient.DoesNotExist:
            pass
    
    return render(request, 'sr.html', context)


# Update the start_workout view to save to database:
@csrf_exempt
def start_workout(request):
    """Start the workout and create database record"""
    global workout_state
    if request.method == 'POST':
        data = json.loads(request.body)
        target_reps = data.get('target_reps', 12)
        
        # Reset workout state
        workout_state['active'] = True
        workout_state['complete'] = False
        workout_state['counter'] = 0
        workout_state['stage'] = None
        workout_state['excellent_reps'] = 0
        workout_state['good_reps'] = 0
        workout_state['partial_reps'] = 0
        workout_state['target_reps'] = target_reps
        workout_state['initial_left_shoulder'] = None
        workout_state['initial_right_shoulder'] = None
        workout_state['start_time'] = time.time()
        workout_state['current_rep'] = {
            "left_min_angle": 180,
            "left_max_angle": 0,
            "left_elbow_angles": [],
            "left_shoulder_elevation": 0,
            "right_min_angle": 180,
            "right_max_angle": 0,
            "right_elbow_angles": [],
            "right_shoulder_elevation": 0,
            "max_asymmetry": 0,
        }
        
        # Create SLS record if patient is logged in
        patient_id = request.session.get('patient_id')
        if patient_id:
            try:
                patient = Patient.objects.get(id=patient_id)
                workout_state['workout_record'] = SLS.objects.create(
                    patient=patient,
                    target_reps=target_reps,
                    date=timezone.now().date()
                )
            except Patient.DoesNotExist:
                workout_state['workout_record'] = None
        else:
            workout_state['workout_record'] = None
        
        return JsonResponse({'status': 'started', 'target_reps': target_reps})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


# Update the get_workout_status view to save progress:
@csrf_exempt
def get_workout_status(request):
    """Get current workout status and update database"""
    global workout_state
    
    # Update database record if it exists
    if workout_state.get('workout_record'):
        try:
            record = workout_state['workout_record']
            record.total_reps = workout_state['counter']
            record.excellent_reps = workout_state['excellent_reps']
            record.good_reps = workout_state['good_reps']
            record.partial_reps = workout_state['partial_reps']
            record.completed = workout_state['complete']
            
            # Calculate duration
            if workout_state.get('start_time'):
                record.duration_seconds = int(time.time() - workout_state['start_time'])
            
            record.save()
        except Exception as e:
            print(f"Error updating SLS record: {e}")
    
    return JsonResponse({
        'active': workout_state['active'],
        'complete': workout_state['complete'],
        'counter': workout_state['counter'],
        'target_reps': workout_state['target_reps'],
        'excellent_reps': workout_state['excellent_reps'],
        'good_reps': workout_state['good_reps'],
        'partial_reps': workout_state['partial_reps'],
    })


# Update the reset_workout view:
@csrf_exempt
def reset_workout(request):
    """Reset workout state and finalize database record"""
    global workout_state
    
    # Finalize the database record before resetting
    if workout_state.get('workout_record'):
        try:
            record = workout_state['workout_record']
            record.total_reps = workout_state['counter']
            record.excellent_reps = workout_state['excellent_reps']
            record.good_reps = workout_state['good_reps']
            record.partial_reps = workout_state['partial_reps']
            record.completed = workout_state['complete']
            
            if workout_state.get('start_time'):
                record.duration_seconds = int(time.time() - workout_state['start_time'])
            
            record.save()
        except Exception as e:
            print(f"Error finalizing SLS record: {e}")
    
    workout_state['active'] = False
    workout_state['complete'] = False
    workout_state['counter'] = 0
    workout_state['excellent_reps'] = 0
    workout_state['good_reps'] = 0
    workout_state['partial_reps'] = 0
    workout_state['workout_record'] = None
    workout_state['start_time'] = None
    
    return JsonResponse({'status': 'reset'})

def jj(request):
    return render(request , 'jj.html')

# ============================================================================
# SIDE LATERAL RAISE - METRICS & CONFIGURATION
# ============================================================================

LEFT_ARM_METRICS = {
    "down_threshold": 35,
    "up_threshold": 100,
    "excellent_peak": 105,
    "good_peak": 95,
    "min_rom": 60,
    "target_elbow": 176,
    "max_elbow_variance": 5,
    "max_shoulder_elevation": 0.025,
}

RIGHT_ARM_METRICS = {
    "down_threshold": 35,
    "up_threshold": 100,
    "excellent_peak": 105,
    "good_peak": 95,
    "min_rom": 60,
    "target_elbow": 175,
    "max_elbow_variance": 5,
    "max_shoulder_elevation": 0.025,
}

SYMMETRY_METRICS = {
    "excellent_threshold": 5,
    "good_threshold": 10,
    "max_allowed": 15,
}

# Global variables for workout tracking
workout_state = {
    'active': False,
    'complete': False,
    'counter': 0,
    'stage': None,
    'excellent_reps': 0,
    'good_reps': 0,
    'partial_reps': 0,
    'target_reps': 12,
    'current_rep': {
        "left_min_angle": 180,
        "left_max_angle": 0,
        "left_elbow_angles": [],
        "left_shoulder_elevation": 0,
        "right_min_angle": 180,
        "right_max_angle": 0,
        "right_elbow_angles": [],
        "right_shoulder_elevation": 0,
        "max_asymmetry": 0,
    },
    'initial_left_shoulder': None,
    'initial_right_shoulder': None,
    'form_warning': '',
    'left_shoulder_angle': 0,
    'right_shoulder_angle': 0,
    'left_elbow_angle': 0,
    'right_elbow_angle': 0,
    'asymmetry': 0,
}

# ============================================================================
# SIDE LATERAL RAISE - HELPER FUNCTIONS
# ============================================================================

def calculate_angle(a, b, c):
    """Calculate angle between three points (a-b-c where b is the vertex)"""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    
    if angle > 180.0:
        angle = 360 - angle
        
    return angle

def get_landmark_coords(landmarks, landmark_id):
    """Extract x, y coordinates from a landmark"""
    landmark = landmarks[landmark_id]
    return [landmark.x, landmark.y]

def calculate_shoulder_elevation(current_shoulder, initial_shoulder):
    """Calculate vertical shoulder movement (shrugging detection)"""
    return abs(current_shoulder[1] - initial_shoulder[1])

def draw_text_with_background(image, text, position, font_scale=0.7, thickness=2, 
                               text_color=(255, 255, 255), bg_color=(0, 0, 0)):
    """Draw text with a background rectangle for better visibility"""
    font = cv2.FONT_HERSHEY_SIMPLEX
    (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    x, y = position
    
    cv2.rectangle(image, (x - 5, y - text_height - 5), 
                  (x + text_width + 5, y + baseline + 5), bg_color, -1)
    
    cv2.putText(image, text, (x, y), font, font_scale, text_color, thickness, cv2.LINE_AA)

# ============================================================================
# SIDE LATERAL RAISE - VIDEO STREAMING
# ============================================================================

def generate_frames():
    """Generate video frames with pose detection and rep counting"""
    global workout_state
    
    mp_drawing = mp.solutions.drawing_utils
    mp_pose = mp.solutions.pose
    
    cap = cv2.VideoCapture(0)
    
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Flip frame horizontally for mirror view
            frame = cv2.flip(frame, 1)
            
            # Convert BGR to RGB
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            
            # Make detection
            results = pose.process(image)
            
            # Convert back to BGR
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            # ================================================================
            # HANDLE WAITING STATE
            # ================================================================
            if not workout_state['active']:
                cv2.rectangle(image, (0, 0), (image.shape[1], image.shape[0]), (50, 50, 50), -1)
                
                draw_text_with_background(image, "CLICK 'START WORKOUT' BUTTON", 
                                        (image.shape[1]//2 - 300, image.shape[0]//2),
                                        font_scale=1.5, thickness=3, 
                                        text_color=(0, 255, 0), bg_color=(0, 0, 0))
                
                draw_text_with_background(image, f"Target: {workout_state['target_reps']} reps | Both arms together", 
                                        (image.shape[1]//2 - 280, image.shape[0]//2 + 60),
                                        font_scale=0.9, thickness=2, 
                                        text_color=(255, 255, 255), bg_color=(0, 0, 0))
            
            # ================================================================
            # ACTIVE WORKOUT
            # ================================================================
            elif workout_state['active'] and not workout_state['complete']:
                try:
                    landmarks = results.pose_landmarks.landmark
                    
                    # Get key points
                    left_shoulder = get_landmark_coords(landmarks, mp_pose.PoseLandmark.LEFT_SHOULDER.value)
                    left_elbow = get_landmark_coords(landmarks, mp_pose.PoseLandmark.LEFT_ELBOW.value)
                    left_wrist = get_landmark_coords(landmarks, mp_pose.PoseLandmark.LEFT_WRIST.value)
                    left_hip = get_landmark_coords(landmarks, mp_pose.PoseLandmark.LEFT_HIP.value)
                    
                    right_shoulder = get_landmark_coords(landmarks, mp_pose.PoseLandmark.RIGHT_SHOULDER.value)
                    right_elbow = get_landmark_coords(landmarks, mp_pose.PoseLandmark.RIGHT_ELBOW.value)
                    right_wrist = get_landmark_coords(landmarks, mp_pose.PoseLandmark.RIGHT_WRIST.value)
                    right_hip = get_landmark_coords(landmarks, mp_pose.PoseLandmark.RIGHT_HIP.value)
                    
                    # Calculate angles
                    left_shoulder_angle = calculate_angle(left_hip, left_shoulder, left_elbow)
                    right_shoulder_angle = calculate_angle(right_hip, right_shoulder, right_elbow)
                    left_elbow_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)
                    right_elbow_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)
                    
                    # Update state
                    workout_state['left_shoulder_angle'] = left_shoulder_angle
                    workout_state['right_shoulder_angle'] = right_shoulder_angle
                    workout_state['left_elbow_angle'] = left_elbow_angle
                    workout_state['right_elbow_angle'] = right_elbow_angle
                    
                    # Calculate asymmetry
                    asymmetry = abs(left_shoulder_angle - right_shoulder_angle)
                    workout_state['asymmetry'] = asymmetry
                    
                    # Set initial shoulder positions
                    if workout_state['initial_left_shoulder'] is None:
                        workout_state['initial_left_shoulder'] = left_shoulder
                        workout_state['initial_right_shoulder'] = right_shoulder
                    
                    # Calculate shoulder elevation
                    left_shoulder_elevation = calculate_shoulder_elevation(
                        left_shoulder, workout_state['initial_left_shoulder'])
                    right_shoulder_elevation = calculate_shoulder_elevation(
                        right_shoulder, workout_state['initial_right_shoulder'])
                    
                    # Track metrics for current rep
                    current_rep = workout_state['current_rep']
                    avg_shoulder_angle = (left_shoulder_angle + right_shoulder_angle) / 2
                    
                    current_rep['left_min_angle'] = min(current_rep['left_min_angle'], left_shoulder_angle)
                    current_rep['left_max_angle'] = max(current_rep['left_max_angle'], left_shoulder_angle)
                    current_rep['right_min_angle'] = min(current_rep['right_min_angle'], right_shoulder_angle)
                    current_rep['right_max_angle'] = max(current_rep['right_max_angle'], right_shoulder_angle)
                    current_rep['max_asymmetry'] = max(current_rep['max_asymmetry'], asymmetry)
                    
                    if workout_state['stage'] == "up":
                        current_rep['left_elbow_angles'].append(left_elbow_angle)
                        current_rep['right_elbow_angles'].append(right_elbow_angle)
                        current_rep['left_shoulder_elevation'] = max(
                            current_rep['left_shoulder_elevation'], left_shoulder_elevation)
                        current_rep['right_shoulder_elevation'] = max(
                            current_rep['right_shoulder_elevation'], right_shoulder_elevation)
                    
                    # Rep detection
                    if avg_shoulder_angle <= LEFT_ARM_METRICS["down_threshold"] and workout_state['stage'] == "up":
                        # Analyze completed rep
                        left_rom = current_rep['left_max_angle'] - current_rep['left_min_angle']
                        right_rom = current_rep['right_max_angle'] - current_rep['right_min_angle']
                        avg_rom = (left_rom + right_rom) / 2
                        avg_peak = (current_rep['left_max_angle'] + current_rep['right_max_angle']) / 2
                        
                        # Calculate elbow consistency
                        left_elbow_std = np.std(current_rep['left_elbow_angles']) if current_rep['left_elbow_angles'] else 0
                        right_elbow_std = np.std(current_rep['right_elbow_angles']) if current_rep['right_elbow_angles'] else 0
                        elbow_consistent = (left_elbow_std < LEFT_ARM_METRICS["max_elbow_variance"] and 
                                          right_elbow_std < RIGHT_ARM_METRICS["max_elbow_variance"])
                        
                        # Check shoulder stability
                        shoulder_stable = (current_rep['left_shoulder_elevation'] <= LEFT_ARM_METRICS["max_shoulder_elevation"] and
                                         current_rep['right_shoulder_elevation'] <= RIGHT_ARM_METRICS["max_shoulder_elevation"])
                        
                        # Check symmetry
                        symmetry_excellent = current_rep['max_asymmetry'] < SYMMETRY_METRICS["excellent_threshold"]
                        symmetry_good = current_rep['max_asymmetry'] < SYMMETRY_METRICS["good_threshold"]
                        
                        # Determine rep quality
                        form_quality = "PARTIAL"
                        
                        if (avg_peak >= LEFT_ARM_METRICS["excellent_peak"] and 
                            avg_rom >= LEFT_ARM_METRICS["min_rom"] and 
                            elbow_consistent and shoulder_stable and symmetry_excellent):
                            form_quality = "EXCELLENT ★"
                            workout_state['excellent_reps'] += 1
                            workout_state['good_reps'] += 1
                        
                        elif (avg_peak >= LEFT_ARM_METRICS["good_peak"] and 
                              avg_rom >= LEFT_ARM_METRICS["min_rom"] and 
                              symmetry_good):
                            form_quality = "GOOD ✓"
                            workout_state['good_reps'] += 1
                        
                        else:
                            workout_state['partial_reps'] += 1
                        
                        workout_state['stage'] = "down"
                        workout_state['counter'] += 1
                        
                        # Reset for next rep
                        workout_state['current_rep'] = {
                            "left_min_angle": 180,
                            "left_max_angle": 0,
                            "left_elbow_angles": [],
                            "left_shoulder_elevation": 0,
                            "right_min_angle": 180,
                            "right_max_angle": 0,
                            "right_elbow_angles": [],
                            "right_shoulder_elevation": 0,
                            "max_asymmetry": 0,
                        }
                        
                        # Check if workout is complete
                        if workout_state['counter'] >= workout_state['target_reps']:
                            workout_state['complete'] = True
                            workout_state['active'] = False
                    
                    elif avg_shoulder_angle >= RIGHT_ARM_METRICS["up_threshold"] and workout_state['stage'] != "up":
                        workout_state['stage'] = "up"
                    
                    # Form warnings
                    form_warning = ""
                    if asymmetry > SYMMETRY_METRICS["max_allowed"]:
                        form_warning = "⚠ UNEVEN ARMS!"
                    elif (left_shoulder_elevation > LEFT_ARM_METRICS["max_shoulder_elevation"] or 
                          right_shoulder_elevation > RIGHT_ARM_METRICS["max_shoulder_elevation"]):
                        form_warning = "⚠ DON'T SHRUG SHOULDERS!"
                    elif workout_state['stage'] == "up":
                        avg_elbow = (left_elbow_angle + right_elbow_angle) / 2
                        if avg_elbow < 165:
                            form_warning = "⚠ KEEP ELBOWS STRAIGHTER!"
                    
                    workout_state['form_warning'] = form_warning
                    
                    # Display angles on arms
                    cv2.putText(image, f'{int(left_shoulder_angle)}°',
                               tuple(np.multiply(left_shoulder, [image.shape[1], image.shape[0]]).astype(int)),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2, cv2.LINE_AA)
                    
                    cv2.putText(image, f'{int(right_shoulder_angle)}°',
                               tuple(np.multiply(right_shoulder, [image.shape[1], image.shape[0]]).astype(int)),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2, cv2.LINE_AA)
                
                except Exception as e:
                    pass
                
                # UI Elements
                cv2.rectangle(image, (0, 0), (500, 280), (100, 100, 100), -1)
                
                cv2.putText(image, 'REPS', (15, 40),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
                cv2.putText(image, f'{workout_state["counter"]}/{workout_state["target_reps"]}', (15, 80),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3, cv2.LINE_AA)
                
                cv2.putText(image, 'STAGE', (200, 40),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
                stage_display = workout_state['stage'].upper() if workout_state['stage'] else '--'
                stage_color = (0, 255, 0) if workout_state['stage'] == "up" else (255, 255, 255)
                cv2.putText(image, stage_display, (200, 80),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.5, stage_color, 3, cv2.LINE_AA)
                
                cv2.putText(image, f'Excellent: {workout_state["excellent_reps"]}', (15, 120),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
                cv2.putText(image, f'Good: {workout_state["good_reps"] - workout_state["excellent_reps"]}', (15, 150),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2, cv2.LINE_AA)
                cv2.putText(image, f'Partial: {workout_state["partial_reps"]}', (15, 180),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2, cv2.LINE_AA)
                
                cv2.putText(image, f'Left: {int(workout_state["left_shoulder_angle"])}°', (15, 220),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(image, f'Right: {int(workout_state["right_shoulder_angle"])}°', (15, 245),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
                
                asym = workout_state['asymmetry']
                asym_color = (0, 255, 0) if asym < SYMMETRY_METRICS["good_threshold"] else (0, 165, 255) if asym < SYMMETRY_METRICS["max_allowed"] else (0, 0, 255)
                cv2.putText(image, f'Diff: {int(asym)}°', (15, 270),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, asym_color, 2, cv2.LINE_AA)
                
                if workout_state['form_warning']:
                    draw_text_with_background(image, workout_state['form_warning'], (15, image.shape[0] - 30),
                                font_scale=0.9, thickness=2, text_color=(0, 0, 255), bg_color=(255, 255, 255))
            
            # Draw pose landmarks
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2))
            
            # Encode frame
            ret, buffer = cv2.imencode('.jpg', image)
            frame = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    cap.release()

# ============================================================================
# SIDE LATERAL RAISE - DJANGO VIEWS
# ============================================================================

# ============================================================================
# SIDE LATERAL RAISE - DJANGO VIEWS
# ============================================================================

def sr(request):
    """Side Lateral Raise dashboard with workout history"""
    patient_id = request.session.get('patient_id')
    
    # Check if user is logged in
    if not patient_id:
        messages.error(request, 'Please log in to view your workout history.')
        return redirect('login')
    
    try:
        patient = Patient.objects.get(id=patient_id)
        
        # Get all SLS workouts for this patient, ordered by date
        sls_workouts = SLS.objects.filter(patient=patient).order_by('date')
        
        # Prepare workout data for the chart (last 10 sessions)
        workout_data = []
        for workout in sls_workouts[:10]:  # Limit to last 10 sessions for clarity
            workout_data.append({
                'date': workout.date.isoformat(),  # Convert to ISO format for JavaScript
                'excellent_reps': workout.excellent_reps,
                'good_reps': workout.good_reps,
                'partial_reps': workout.partial_reps,
                'total_reps': workout.total_reps,
                'completion_percentage': workout.completion_percentage,
                'quality_score': workout.quality_score
            })
        
        # If no data exists, provide sample data
        if not workout_data:
            workout_data = [
                {
                    'date': (date.today() - timedelta(days=6)).isoformat(),
                    'excellent_reps': 0,
                    'good_reps': 0,
                    'partial_reps': 0,
                    'total_reps': 0,
                    'completion_percentage': 0,
                    'quality_score': 0
                }
            ]
        
        context = {
            'patient': patient,
            'workout_data': json.dumps(workout_data),  # Convert to JSON for JavaScript
        }
        
        return render(request, 'sr.html', context)
        
    except Patient.DoesNotExist:
        messages.error(request, 'Session expired. Please log in again.')
        return redirect('login')
    

def reset_workout(request):
    if request.method == "POST":
        # Here you can reset any session or database flags
        return JsonResponse({"status": "reset"})
    return JsonResponse({"status": "error"}, status=400)

def get_workout_status(request):
    # Dummy example; replace with actual tracking logic
    status = request.session.get('workout_status', {
        'counter': 0,
        'target_reps': 12,
        'excellent_reps': 0,
        'good_reps': 0,
        'partial_reps': 0,
        'complete': False
    })
    return JsonResponse(status)

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .models import SLS, Patient  # Adjust according to your model

@csrf_exempt
def save_workout(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Example: save to database (adjust fields as needed)
            patient = Patient.objects.first()  # Replace with actual patient
            sls = SLS.objects.create(
                patient=patient,
                total_reps=data.get('total_reps', 0),
                target_reps=data.get('target_reps', 0),
                excellent_reps=data.get('excellent_reps', 0),
                good_reps=data.get('good_reps', 0),
                partial_reps=data.get('partial_reps', 0),
                completed=data.get('completed', False)
            )
            return JsonResponse({'status': 'success', 'workout_id': sls.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)})
    return JsonResponse({'status': 'error', 'error': 'Invalid request method'})




def srtwo(request):
    """Side Lateral Raise tracker main view"""
    return render(request, 'side_lateral_raise.html')

def video_feed(request):
    """Video streaming route"""
    return StreamingHttpResponse(generate_frames(),
                                content_type='multipart/x-mixed-replace; boundary=frame')

@csrf_exempt
def start_workout(request):
    """Start the workout"""
    global workout_state
    if request.method == 'POST':
        data = json.loads(request.body)
        target_reps = data.get('target_reps', 12)
        
        # Reset workout state
        workout_state['active'] = True
        workout_state['complete'] = False
        workout_state['counter'] = 0
        workout_state['stage'] = None
        workout_state['excellent_reps'] = 0
        workout_state['good_reps'] = 0
        workout_state['partial_reps'] = 0
        workout_state['target_reps'] = target_reps
        workout_state['initial_left_shoulder'] = None
        workout_state['initial_right_shoulder'] = None
        workout_state['current_rep'] = {
            "left_min_angle": 180,
            "left_max_angle": 0,
            "left_elbow_angles": [],
            "left_shoulder_elevation": 0,
            "right_min_angle": 180,
            "right_max_angle": 0,
            "right_elbow_angles": [],
            "right_shoulder_elevation": 0,
            "max_asymmetry": 0,
        }
        
        return JsonResponse({'status': 'started', 'target_reps': target_reps})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def save_workout(request):
    """Save completed workout to database"""
    if request.method == 'POST':
        try:
            patient_id = request.session.get('patient_id')
            
            if not patient_id:
                return JsonResponse({'error': 'Not authenticated'}, status=401)
            
            patient = Patient.objects.get(id=patient_id)
            data = json.loads(request.body)
            
            # Create new SLS workout entry
            workout = SLS.objects.create(
                patient=patient,
                date=date.today(),
                total_reps=data.get('total_reps', 0),
                target_reps=data.get('target_reps', 10),
                excellent_reps=data.get('excellent_reps', 0),
                good_reps=data.get('good_reps', 0),
                partial_reps=data.get('partial_reps', 0),
                duration_seconds=data.get('duration_seconds', 0),
                completed=data.get('completed', False)
            )
            
            return JsonResponse({
                'status': 'success',
                'workout_id': workout.id,
                'message': 'Workout saved successfully!'
            })
            
        except Patient.DoesNotExist:
            return JsonResponse({'error': 'Patient not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def reset_workout(request):
    """Reset the workout state"""
    global workout_state
    if request.method == 'POST':
        # Reset all workout state
        workout_state['active'] = False
        workout_state['complete'] = False
        workout_state['counter'] = 0
        workout_state['stage'] = None
        workout_state['excellent_reps'] = 0
        workout_state['good_reps'] = 0
        workout_state['partial_reps'] = 0
        workout_state['target_reps'] = 12
        workout_state['initial_left_shoulder'] = None
        workout_state['initial_right_shoulder'] = None
        workout_state['left_shoulder_angle'] = 0
        workout_state['right_shoulder_angle'] = 0
        workout_state['asymmetry'] = 0
        workout_state['form_warning'] = ""
        workout_state['current_rep'] = {
            "left_min_angle": 180,
            "left_max_angle": 0,
            "left_elbow_angles": [],
            "left_shoulder_elevation": 0,
            "right_min_angle": 180,
            "right_max_angle": 0,
            "right_elbow_angles": [],
            "right_shoulder_elevation": 0,
            "max_asymmetry": 0,
        }
        
        return JsonResponse({'status': 'reset'})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def get_workout_status(request):
    """Get current workout status"""
    global workout_state
    
    return JsonResponse({
        'counter': workout_state['counter'],
        'stage': workout_state['stage'],
        'excellent_reps': workout_state['excellent_reps'],
        'good_reps': workout_state['good_reps'],
        'partial_reps': workout_state['partial_reps'],
        'target_reps': workout_state['target_reps'],
        'complete': workout_state['complete'],
        'active': workout_state['active'],
        'left_shoulder_angle': int(workout_state['left_shoulder_angle']),
        'right_shoulder_angle': int(workout_state['right_shoulder_angle']),
        'asymmetry': int(workout_state['asymmetry']),
        'form_warning': workout_state['form_warning']
    })
# ============================================================================
# BICEP CURL WORKOUT TRACKING
# ============================================================================

bicep_state = {
    'counter': 0,
    'stage': None, 
    'active': False,
    'complete': False,
    'target_reps': 10,
    'excellent_reps': 0, # Full ROM
    'good_reps': 0,
    'partial_reps': 0,
    'left_angle': 0,
    'right_angle': 0,
    'form_warning': "",
    'feedback': "",
}

def generate_bicep_frames():
    """Generate video frames for Bicep Curl with pose detection"""
    global bicep_state
    
    # Try to import mediapipe solutions securely
    try:
        import mediapipe as mp
        mp_drawing = mp.solutions.drawing_utils
        mp_pose = mp.solutions.pose
    except (ImportError, AttributeError):
        # Fallback if mediapipe is broken
        cap = cv2.VideoCapture(0)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            cv2.putText(frame, "Mediapipe Not Available", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        cap.release()
        return

    cap = cv2.VideoCapture(0)
    
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            
            # Process frame
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = pose.process(image)
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            try:
                landmarks = results.pose_landmarks.landmark
                
                # Get coordinates
                left_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                left_elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                left_wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
                
                right_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                right_elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                right_wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
                
                # Calculate angles
                left_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)
                right_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)
                
                # Update State logic (Focus on one detected arm or both)
                # Simple logic: Use arm with better visibility or just first available
                # For simplicity: Check Right arm (change as needed)
                
                # Update global state for UI
                bicep_state['right_angle'] = right_angle
                bicep_state['left_angle'] = left_angle
                
                # Logic for Right Arm
                angle = right_angle
                stage = bicep_state['stage']
                
                if angle > 160:
                    bicep_state['stage'] = "down"
                    bicep_state['feedback'] = "Good extension"
                if angle < 30 and stage == 'down':
                    bicep_state['stage'] = "up"
                    bicep_state['counter'] += 1
                    bicep_state['feedback'] = "Good curl!"
                    # TODO: Add quality grading logic here
                    
                # Visualize
                cv2.rectangle(image, (0,0), (225,73), (245,117,16), -1)
                cv2.putText(image, str(bicep_state['counter']), (10,60), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2, cv2.LINE_AA)
                cv2.putText(image, bicep_state['stage'], (60,60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
                
                # Draw landmarks
                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                
            except Exception as e:
                pass
                
            ret, buffer = cv2.imencode('.jpg', image)
            frame = buffer.tobytes()
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()

@csrf_exempt
def start_bicep_workout(request):
    global bicep_state
    if request.method == 'POST':
        data = json.loads(request.body)
        bicep_state['target_reps'] = data.get('target_reps', 10)
        bicep_state['counter'] = 0
        bicep_state['active'] = True
        return JsonResponse({'status': 'started'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def reset_bicep_workout(request):
    global bicep_state
    bicep_state['counter'] = 0
    bicep_state['active'] = False
    return JsonResponse({'status': 'reset'})

def get_bicep_status(request):
    global bicep_state
    return JsonResponse(bicep_state)

def bicep_feed_view(request):
    return StreamingHttpResponse(generate_bicep_frames(), content_type='multipart/x-mixed-replace; boundary=frame')
