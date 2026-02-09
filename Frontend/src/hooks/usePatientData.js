import { useState, useEffect } from 'react';
import djangoAPI from '../services/djangoApi';

/**
 * Custom hook to fetch and manage patient dashboard data
 * @returns {Object} { patient, loading, error, refetch }
 */
export const usePatientData = () => {
    const [patient, setPatient] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchPatientData = async () => {
        try {
            setLoading(true);
            setError(null);

            const response = await djangoAPI.patient.getDashboard();

            if (response && response.patient) {
                setPatient(response.patient);
            }
        } catch (err) {
            console.error('Error fetching patient data:', err);
            setError(err.message || 'Failed to load patient data');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchPatientData();
    }, []);

    return {
        patient,
        loading,
        error,
        refetch: fetchPatientData,
    };
};

export default usePatientData;
