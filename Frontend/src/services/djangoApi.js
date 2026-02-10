// API Service for connecting React to Django Backend
// This file uses the new JSON API endpoints (/api/*)

import { API_URL } from '../config/api';

// When using Vite proxy, we don't need the full URL - proxy handles it
// However, the user wants us to use the VITE_API_URL environment variable
const API_BASE_URL = API_URL;

// Helper to get CSRF token from cookies
const getCSRFToken = () => {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
};

// Generic API call helper for JSON endpoints
const apiCall = async (endpoint, method = 'GET', data = null) => {
    const csrfToken = getCSRFToken();

    const config = {
        method,
        credentials: 'include', // Important for session-based auth
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            ...(csrfToken && { 'X-CSRFToken': csrfToken })
        },
    };

    if (data && method !== 'GET') {
        config.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

        // Handle different response types
        if (response.status === 204) {
            return { success: true };
        }

        const responseData = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(responseData.error || responseData.message || `API Error: ${response.statusText}`);
        }

        return responseData;
    } catch (error) {
        console.error(`API call failed for ${endpoint}:`, error);
        throw error;
    }
};

// Fetch CSRF token from Django
export const fetchCSRFToken = async () => {
    try {
        // Make a simple GET request to get the CSRF token cookie
        await fetch(`${API_BASE_URL}/api/health/`, {
            credentials: 'include'
        });
    } catch (error) {
        console.error('Failed to fetch CSRF token:', error);
    }
};

// ==================== Patient API ====================

export const patientAPI = {
    // Patient login using new JSON API
    login: async (email, password) => {
        // First, get CSRF token
        await fetchCSRFToken();

        // Use the new JSON API endpoint
        return apiCall('/api/patient/login/', 'POST', { email, password });
    },

    // Get current logged-in patient dashboard data
    getDashboard: async () => {
        return apiCall('/api/patient/dashboard/');
    },

    // Get patient profile
    getProfile: async () => {
        return apiCall('/api/patient/profile/');
    },

    // Logout patient
    logout: async () => {
        return apiCall('/api/patient/logout/', 'POST');
    },
};

// ==================== Doctor API ====================

export const doctorAPI = {
    // Get all patients
    getPatients: async () => {
        return apiCall('/api/patients/');
    },

    // Add new patient
    addPatient: async (patientData) => {
        return apiCall('/api/patients/add/', 'POST', patientData);
    },

    // Old endpoints (HTML-based, may not work with React)
    getPortal: async () => {
        return apiCall('/doc_port/');
    },

    getInfoPage: async () => {
        return apiCall('/doc_info_page/');
    },

    submitPatientInfo: async (patientData) => {
        return apiCall('/doctor_info', 'POST', patientData);
    },
};

// ==================== Chatbot API ====================

export const chatbotAPI = {
    // Send message to chatbot
    sendMessage: async (message, language = 'english') => {
        return apiCall('/patient/chatbot/send/', 'POST', { message, language });
    },
};

// ==================== Exercise API ====================

export const exerciseAPI = {
    // Get list of exercises using new API
    getExercises: async () => {
        return apiCall('/api/exercises/');
    },

    // Get exercise history
    getHistory: async () => {
        return apiCall('/api/exercises/history/');
    },

    // Workout control endpoints (these return JSON already)
    startWorkout: async (targetReps = 12) => {
        return apiCall('/sr/start/', 'POST', { target_reps: targetReps });
    },

    getWorkoutStatus: async () => {
        return apiCall('/sr/status/');
    },

    resetWorkout: async () => {
        return apiCall('/sr/reset/', 'POST');
    },

    saveWorkout: async () => {
        return apiCall('/sr/save/', 'POST');
    },

    // Video feed URL (streaming endpoint, not JSON)
    getVideoFeedUrl: () => {
        return `${API_BASE_URL}/sr/video_feed/`;
    },

    // Bicep Curl Methods
    startBicepWorkout: async (targetReps = 10) => {
        return apiCall('/bc/start/', 'POST', { target_reps: targetReps });
    },

    getBicepStatus: async () => {
        return apiCall('/bc/status/');
    },

    resetBicepWorkout: async () => {
        return apiCall('/bc/reset/', 'POST');
    },

    getBicepVideoFeedUrl: () => {
        return `${API_BASE_URL}/bc/video_feed/`;
    },

    updateSessionData: async (data) => {
        return apiCall('/api/exercises/update-session/', 'POST', data);
    },
};

// ==================== Health Check API ====================

export const healthAPI = {
    check: async () => {
        return apiCall('/api/health/');
    },
};

// ==================== Combined Export ====================

const djangoAPI = {
    patient: patientAPI,
    doctor: doctorAPI,
    chatbot: chatbotAPI,
    exercise: exerciseAPI,
    health: healthAPI,
};

export default djangoAPI;

// ==================== Utility Functions ====================

// Check if user is authenticated (has active session)
export const isAuthenticated = async () => {
    try {
        const response = await patientAPI.getDashboard();
        return response?.success === true;
    } catch (error) {
        return false;
    }
};

// Handle API errors with user-friendly messages
export const handleAPIError = (error) => {
    if (error.message.includes('401') || error.message.includes('Not authenticated')) {
        return 'Please log in to access this page.';
    }

    if (error.message.includes('403')) {
        return 'You do not have permission to perform this action.';
    }

    if (error.message.includes('404')) {
        return 'The requested resource was not found.';
    }

    if (error.message.includes('500')) {
        return 'Server error. Please try again later.';
    }

    return error.message || 'An unexpected error occurred.';
};
