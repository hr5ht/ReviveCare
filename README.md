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
*   **React**: Core framework for building a dynamic user interface.
*   **Vite**: Next-generation frontend tooling for fast build times.
*   **Tailwind CSS**: Utility-first CSS framework for a modern, responsive design.
*   **React Router**: For seamless navigation between application views.

### Backend
*   **Django**: High-level Python web framework for robust backend logic.
*   **MediaPipe & OpenCV**: Advanced computer vision libraries used for pose detection and real-time exercise tracking.
*   **LangChain & Sarvam AI**: Integration frameworks for the AI chat assistant capabilities.
*   **SQLite**: Lightweight database for local development and data storage.

## Getting Started

Follow these instructions to set up the project locally on your machine.

### Prerequisites
*   Node.js (v18 or higher)
*   Python (v3.10 or higher)
*   Git

### Installation

1.  **Clone the repository**
    ```bash
    git clone <repository-url>
    cd ReviveCare
    ```

2.  **Backend Setup**
    Navigate to the backend directory and set up the Python environment.

    ```bash
    cd Backend
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

    Run the database migrations and start the server:
    ```bash
    python manage.py migrate
    python manage.py runserver
    ```
    The backend will run at `http://127.0.0.1:8000`.

3.  **Frontend Setup**
    Open a new terminal, navigate to the frontend directory, and install dependencies.

    ```bash
    cd Frontend
    npm install
    ```

    Start the development server:
    ```bash
    npm run dev
    ```
    The frontend will usually be accessible at `http://localhost:5173`.

## Usage

1.  Ensure both the Backend (Django) and Frontend (Vite) servers are running.
2.  Open your browser and navigate to the frontend URL (e.g., `http://localhost:5173`).
3.  **Doctors**: Navigate to the Doctor Dashboard to manage patients.
4.  **Patients**: Login to access the exercise tracker. Select an exercise to start the video feed. Ensure your webcam is enabled and you are visible in the frame for the AI tracking to work correctly.

## Contributing

Contributions are welcome. If you have suggestions for improvements or new features, please feel free to submit a pull request or open an issue for discussion.

## License

This project is licensed under the MIT License.
