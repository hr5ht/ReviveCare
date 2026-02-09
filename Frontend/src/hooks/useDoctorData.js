import { useState, useCallback } from 'react';
import djangoAPI from '../services/djangoApi';

/**
 * Custom hook for doctor operations
 * @returns {Object} { submitPatientInfo, loading, error, success }
 */
export const useDoctorData = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(false);

    const submitPatientInfo = useCallback(async (patientData) => {
        try {
            setLoading(true);
            setError(null);
            setSuccess(false);

            const response = await djangoAPI.doctor.submitPatientInfo(patientData);

            if (response && response.success) {
                setSuccess(true);
                return {
                    success: true,
                    created: response.created,
                    message: response.created
                        ? 'Patient created successfully!'
                        : 'Patient updated successfully!'
                };
            }

            return { success: false, message: 'Failed to save patient information' };
        } catch (err) {
            console.error('Error submitting patient info:', err);
            setError(err.message || 'Failed to submit patient information');
            return { success: false, message: err.message };
        } finally {
            setLoading(false);
        }
    }, []);

    const resetState = useCallback(() => {
        setError(null);
        setSuccess(false);
    }, []);

    return {
        submitPatientInfo,
        loading,
        error,
        success,
        resetState,
    };
};

export default useDoctorData;
