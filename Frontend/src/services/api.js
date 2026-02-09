// API Service for ReviveCare Frontend
// This file handles all communication with the Django backend

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Helper function for making API calls with authentication
const apiCall = async (endpoint, method = 'GET', data = null, isFormData = false) => {
    const token = localStorage.getItem('authToken');

    const config = {
        method,
        headers: {
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...(!isFormData && { 'Content-Type': 'application/json' })
        },
    };

    if (data) {
        config.body = isFormData ? data : JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `API Error: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`API call failed for ${endpoint}:`, error);
        throw error;
    }
};

// ==================== Authentication ====================

export const authAPI = {
    login: (email, password, role = 'patient') =>
        apiCall('/auth/login/', 'POST', { email, password, role }),

    register: (userData) =>
        apiCall('/auth/register/', 'POST', userData),

    logout: () =>
        apiCall('/auth/logout/', 'POST'),

    getCurrentUser: () =>
        apiCall('/auth/user/'),

    refreshToken: () =>
        apiCall('/auth/refresh/', 'POST'),
};

// ==================== Patients ====================

export const patientsAPI = {
    // Get all patients (for doctors)
    getAll: () =>
        apiCall('/patients/'),

    // Get single patient details
    getById: (id) =>
        apiCall(`/patients/${id}/`),

    // Get current patient profile (for logged-in patient)
    getProfile: () =>
        apiCall('/patients/profile/'),

    // Create new patient
    create: (patientData) =>
        apiCall('/patients/', 'POST', patientData),

    // Update patient
    update: (id, patientData) =>
        apiCall(`/patients/${id}/`, 'PUT', patientData),

    // Delete patient
    delete: (id) =>
        apiCall(`/patients/${id}/`, 'DELETE'),

    // Get patient's progress data
    getProgress: (id) =>
        apiCall(`/patients/${id}/progress/`),

    // Get patient's weekly stats
    getWeeklyStats: (id) =>
        apiCall(`/patients/${id}/weekly-stats/`),
};

// ==================== Exercises ====================

export const exercisesAPI = {
    // Get all exercises from library
    getAll: () =>
        apiCall('/exercises/'),

    // Get exercise by ID
    getById: (id) =>
        apiCall(`/exercises/${id}/`),

    // Create new exercise (for admins/doctors)
    create: (exerciseData) =>
        apiCall('/exercises/', 'POST', exerciseData),

    // Update exercise
    update: (id, exerciseData) =>
        apiCall(`/exercises/${id}/`, 'PUT', exerciseData),

    // Delete exercise
    delete: (id) =>
        apiCall(`/exercises/${id}/`, 'DELETE'),

    // Upload exercise video
    uploadVideo: (id, videoFile) => {
        const formData = new FormData();
        formData.append('video', videoFile);
        return apiCall(`/exercises/${id}/upload-video/`, 'POST', formData, true);
    },

    // Get exercises by category
    getByCategory: (category) =>
        apiCall(`/exercises/?category=${category}`),
};

// ==================== Patient Exercises (Assignments) ====================

export const patientExercisesAPI = {
    // Get all assigned exercises for current patient
    getAssigned: () =>
        apiCall('/patient-exercises/'),

    // Get assigned exercises for specific patient (for doctors)
    getForPatient: (patientId) =>
        apiCall(`/patient-exercises/?patient=${patientId}`),

    // Assign exercise to patient
    assign: (patientId, exerciseId, instructions = null) =>
        apiCall('/patient-exercises/', 'POST', {
            patient: patientId,
            exercise: exerciseId,
            instructions
        }),

    // Mark exercise as completed
    markComplete: (id, completionData = {}) =>
        apiCall(`/patient-exercises/${id}/complete/`, 'PUT', {
            completed: true,
            completion_date: new Date().toISOString(),
            ...completionData
        }),

    // Update exercise assignment
    update: (id, updateData) =>
        apiCall(`/patient-exercises/${id}/`, 'PUT', updateData),

    // Remove exercise assignment
    remove: (id) =>
        apiCall(`/patient-exercises/${id}/`, 'DELETE'),

    // Get completion history
    getHistory: (patientId = null) => {
        const endpoint = patientId
            ? `/patient-exercises/history/?patient=${patientId}`
            : '/patient-exercises/history/';
        return apiCall(endpoint);
    },
};

// ==================== AI Chat ====================

export const chatAPI = {
    // Send message to AI assistant
    sendMessage: (message, patientId = null) =>
        apiCall('/chat/', 'POST', { message, patient_id: patientId }),

    // Get chat history
    getHistory: (patientId = null, limit = 50) => {
        const endpoint = patientId
            ? `/chat/history/?patient=${patientId}&limit=${limit}`
            : `/chat/history/?limit=${limit}`;
        return apiCall(endpoint);
    },

    // Trigger manual doctor alert
    alertDoctor: (patientId, message, urgency = 'normal') =>
        apiCall('/chat/alert-doctor/', 'POST', {
            patient_id: patientId,
            message,
            urgency
        }),

    // Clear chat history
    clearHistory: () =>
        apiCall('/chat/history/', 'DELETE'),
};

// ==================== Prescriptions ====================

export const prescriptionsAPI = {
    // Get all prescriptions for current patient
    getAll: () =>
        apiCall('/prescriptions/'),

    // Get prescriptions for specific patient (for doctors)
    getForPatient: (patientId) =>
        apiCall(`/prescriptions/?patient=${patientId}`),

    // Get single prescription
    getById: (id) =>
        apiCall(`/prescriptions/${id}/`),

    // Create prescription
    create: (prescriptionData) =>
        apiCall('/prescriptions/', 'POST', prescriptionData),

    // Update prescription
    update: (id, prescriptionData) =>
        apiCall(`/prescriptions/${id}/`, 'PUT', prescriptionData),

    // Delete prescription
    delete: (id) =>
        apiCall(`/prescriptions/${id}/`, 'DELETE'),

    // Mark medication as taken
    markTaken: (id, timestamp = null) =>
        apiCall(`/prescriptions/${id}/mark-taken/`, 'POST', {
            taken_at: timestamp || new Date().toISOString()
        }),
};

// ==================== Doctors ====================

export const doctorsAPI = {
    // Get doctor's profile
    getProfile: () =>
        apiCall('/doctors/profile/'),

    // Update doctor's profile
    updateProfile: (profileData) =>
        apiCall('/doctors/profile/', 'PUT', profileData),

    // Get doctor's patients
    getPatients: () =>
        apiCall('/doctors/patients/'),

    // Get doctor's statistics
    getStats: () =>
        apiCall('/doctors/stats/'),

    // Get pending alerts
    getAlerts: () =>
        apiCall('/doctors/alerts/'),

    // Mark alert as read
    markAlertRead: (alertId) =>
        apiCall(`/doctors/alerts/${alertId}/read/`, 'PUT'),
};

// ==================== Notifications ====================

export const notificationsAPI = {
    // Get all notifications
    getAll: () =>
        apiCall('/notifications/'),

    // Get unread notifications
    getUnread: () =>
        apiCall('/notifications/?unread=true'),

    // Mark notification as read
    markRead: (id) =>
        apiCall(`/notifications/${id}/read/`, 'PUT'),

    // Mark all as read
    markAllRead: () =>
        apiCall('/notifications/mark-all-read/', 'PUT'),

    // Delete notification
    delete: (id) =>
        apiCall(`/notifications/${id}/`, 'DELETE'),
};

// ==================== Analytics ====================

export const analyticsAPI = {
    // Get patient analytics
    getPatientAnalytics: (patientId, dateRange = 'week') =>
        apiCall(`/analytics/patient/${patientId}/?range=${dateRange}`),

    // Get doctor analytics
    getDoctorAnalytics: (dateRange = 'month') =>
        apiCall(`/analytics/doctor/?range=${dateRange}`),

    // Get exercise completion rates
    getCompletionRates: (patientId = null) => {
        const endpoint = patientId
            ? `/analytics/completion-rates/?patient=${patientId}`
            : '/analytics/completion-rates/';
        return apiCall(endpoint);
    },
};

// ==================== Export all APIs ====================

const API = {
    auth: authAPI,
    patients: patientsAPI,
    exercises: exercisesAPI,
    patientExercises: patientExercisesAPI,
    chat: chatAPI,
    prescriptions: prescriptionsAPI,
    doctors: doctorsAPI,
    notifications: notificationsAPI,
    analytics: analyticsAPI,
};

export default API;

// ==================== Utility Functions ====================

// Handle API errors with user-friendly messages
export const handleAPIError = (error) => {
    if (error.message.includes('401')) {
        // Unauthorized - redirect to login
        localStorage.removeItem('authToken');
        window.location.href = '/login';
        return 'Session expired. Please log in again.';
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

// Check if user is authenticated
export const isAuthenticated = () => {
    return !!localStorage.getItem('authToken');
};

// Get user role
export const getUserRole = () => {
    return localStorage.getItem('userRole');
};

// Set auth token
export const setAuthToken = (token) => {
    localStorage.setItem('authToken', token);
};

// Clear auth data
export const clearAuthData = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userRole');
};