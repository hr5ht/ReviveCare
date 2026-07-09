# ReviveCare

ReviveCare is a comprehensive healthcare platform designed to bridge the gap between patients and doctors through advanced technology. It combines AI-driven rehabilitation tracking, a smart conversational assistant, and efficient patient management into a unified experience.

This application leverages computer vision to provide real-time feedback on physical therapy exercises, ensuring patients perform their routines correctly and safe at home. Simultaneously, it offers doctors a streamlined dashboard to monitor patient progress and manage care plans effectively.

## Features

### For Patients
*   **AI-Powered Exercise Tracking**: Real-time monitoring of rehabilitation exercises (such as Bicep Curls) using computer vision. The system provides immediate feedback on form and counts repetitions automatically via webcam.
*   **Intelligent Chat Assistant**: An integrated AI chatbot capable of answering health-related queries and providing guidance, powered by advanced language models.
*   **Personalized Dashboard**: A clear, accessible interface to view assigned exercises, track progress, and manage personal health data.

### For Doctors
*   **Patient Management Dashboard**: A centralized hub to add new patients, review patient profiles, and assign treatment plans.
*   **Progress Monitoring**: Tools to track patient adherence to exercise routines and recovery milestones.

## Technology Stack

### Frontend
*   **Django templates** (`Backend/templates/`): Plain HTML, CSS and JavaScript served by Django. No build step.
*   **Tailwind CSS v4** (browser build via CDN) and **Lucide** icons.
*   **MediaPipe Pose** (CDN) for in-browser exercise tracking.

### Backend
*   **Django**: High-level Python web framework for robust backend logic.
*   **MediaPipe & OpenCV**: Advanced computer vision libraries used for pose detection and real-time exercise tracking.
*   **LangChain & Sarvam AI**: Integration frameworks for the AI chat assistant capabilities.
*   **SQLite / PostgreSQL**: SQLite locally, NeonDB (Postgres) in production via `DATABASE_URL`.

## Getting Started

Follow these instructions to set up the project locally on your machine.

### Prerequisites
*   Python 3.11 or higher
*   Git

### Installation

1.  **Clone the repository**
    ```bash
    git clone <repository-url>
    cd ReviveCare
    ```

2.  **Setup**
    ```bash
    cd Backend
    python3.11 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    cp .env.example .env      # then fill in DATABASE_URL, GROQ_API_KEY, etc.
    ```

3.  **Run**
    ```bash
    python manage.py migrate
    python manage.py runserver
    ```
    Open `http://127.0.0.1:8000`. The pages and the API are both served by Django.

### Deploy (Vercel)

Vercel detects Django from `Backend/manage.py`, runs `collectstatic`, and serves static files from its CDN.

```bash
cd Backend
vercel        # pick "Django" as the framework; root directory is Backend
vercel --prod
```

Set the environment variables below in the Vercel project. In production you need at least `SECRET_KEY` and `DATABASE_URL`. Leave `DEBUG` and `COOKIE_SECURE` unset there.

Production builds run `python manage.py migrate` before going live (`Backend/build.py`, hooked up in `Backend/pyproject.toml`).

#### Preview deployments on a Neon branch

Give previews their own database so test data and unmerged migrations never reach production:

1. In the Neon console, create a branch from `main` (for example `preview`) and copy its connection string.
2. In Vercel → Settings → Environment Variables, add `PREVIEW_DATABASE_URL` with that string, scoped to **Preview** only.
3. Redeploy a preview. Its build migrates the branch, and the app reads and writes only the branch.

Without `PREVIEW_DATABASE_URL`, previews use `DATABASE_URL` (production) and skip migrations, so code that needs a new migration will fail there instead of changing the production schema. To refresh the branch with current production data, reset it from its parent in the Neon console.

### Environment variables

All are read in `Backend/ReviveCare/settings.py` or where noted. `Backend/.env.example` lists them with local defaults; copy it to `Backend/.env`.

| Variable | Needed | What it does |
|---|---|---|
| `SECRET_KEY` | Production | Django's signing key. Without it the app refuses to start unless `DEBUG=True`. |
| `DEBUG` | Local only | `True` for development: detailed errors and a built-in fallback secret key. |
| `DATABASE_URL` | Production | Database connection string: Neon Postgres in production, `sqlite:///db.sqlite3` locally. |
| `PREVIEW_DATABASE_URL` | Optional | Neon branch used by Vercel Preview deployments instead of `DATABASE_URL`. |
| `COOKIE_SECURE` | Local only | `False` lets session cookies work over plain `http://localhost`. |
| `SITE_URL` | Recommended | Public address used in links inside emails sent by the scheduled commands. |
| `LOG_LEVEL` | Optional | Root log level (default `INFO`). Requests are logged as one JSON line each. |
| `GROQ_API_KEY` | For chat | Key for the recovery assistant (Groq). Without it the chat replies with a fallback message. |
| `GROQ_MODEL` | Optional | Groq model name (default `openai/gpt-oss-120b`). |
| `EMAIL_PASSWORD` | For email | SMTP password (a Gmail app password). Without it emails are printed to the console. |
| `EMAIL_SENDER`, `SMTP_SERVER`, `SMTP_PORT` | Optional | Sending address and SMTP server (default Gmail on port 587). |
| `DOCTOR_EMAIL` | Optional | Where chat alerts go when a patient has no doctor with an email address. |
| `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` | For SMS | Text doctors about serious alerts. All three are needed. |
| `TO_NUMBER` | Optional | SMS fallback when the doctor's profile has no phone number. |
| `SENTRY_DSN` | Optional | Report errors to Sentry. No request bodies, cookies or personal data are sent. |
| `SENTRY_TRACES_SAMPLE_RATE` | Optional | Share of requests traced for performance, 0 to 1 (default 0). |
| `HSTS_SECONDS` | Optional | Turn on HSTS once the custom domain serves HTTPS everywhere. Start at 3600. |
| `HSTS_INCLUDE_SUBDOMAINS`, `HSTS_PRELOAD` | Optional | HSTS flags (defaults `True` and `False`). |

Vercel sets `VERCEL_ENV` and `VERCEL_GIT_COMMIT_SHA` itself; they choose the preview database, gate build-time migrations and tag Sentry releases.

## Usage

1.  Start the Django server.
2.  Open `http://127.0.0.1:8000` in your browser.
3.  **Doctors**: Navigate to the Doctor Dashboard to manage patients.
4.  **Patients**: Login to access the exercise tracker. Select an exercise to start the video feed. Ensure your webcam is enabled and you are visible in the frame for the AI tracking to work correctly.

## Contributing

Contributions are welcome. If you have suggestions for improvements or new features, please feel free to submit a pull request or open an issue for discussion.

## License

This project is licensed under the MIT License.
