import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';

// Import page components
import ReviveCare from './pages/ReviveCare';
import MedicalDashboard from './pages/MedicalDashboard';
import DoctorDashboard from './pages/DoctorDashboard';
import PatientDashboard from './pages/PatientDashboard';
import PatientDashboardsimple from './pages/PatientDashboardsimple';
import PatientLogin from './pages/PatientLogin';
import AddPatientForm from './pages/AddPatientForm';
import AddPatientFormStandalone from './pages/AddPatientFormStandalone';
import ChatInterface from './pages/ChatInterface';
import ExerciseSelection from './pages/ExerciseSelection';
import ExerciseWorkout from './pages/ExerciseWorkout';

/**
 * Main App Component
 * Handles routing for the ReviveCare application
 */
function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Landing Page */}
          <Route path="/" element={<ReviveCare />} />

          {/* Dashboard Routes */}
          <Route path="/medical-dashboard" element={<MedicalDashboard />} />
          <Route path="/doctor" element={<DoctorDashboard />} />

          {/* Patient Routes */}
          <Route path="/patient/login" element={<PatientLogin />} />
          <Route path="/patient/dashboard" element={<PatientDashboard />} />
          <Route path="/patient" element={<Navigate to="/patient/login" replace />} />
          <Route path="/patient/simple" element={<PatientDashboardsimple />} />

          {/* Exercise Routes */}
          <Route path="/patient/exercises" element={<ExerciseSelection />} />
          <Route path="/patient/exercise/:exerciseId" element={<ExerciseWorkout />} />

          {/* Chat Interface Route - Patient AI Assistant */}
          <Route path="/patient/chat" element={<ChatInterface />} />
          <Route path="/chat" element={<ChatInterface />} />

          {/* Form Routes */}
          <Route path="/doctor/add-patient" element={<AddPatientForm />} />
          <Route path="/add-patient/standalone" element={<AddPatientFormStandalone />} />

          {/* Redirect unknown routes to home */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;