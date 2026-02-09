import React, { createContext, useContext, useState, useEffect } from 'react';
import djangoAPI from '../services/djangoApi';

const AuthContext = createContext(null);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Check if user is already logged in on mount
    useEffect(() => {
        checkAuthStatus();
    }, []);

    const checkAuthStatus = async () => {
        try {
            console.log('[AuthContext] Checking authentication status...');
            setLoading(true);

            const response = await djangoAPI.patient.getDashboard();
            console.log('[AuthContext] Dashboard API response:', response);

            if (response?.success && response?.patient) {
                console.log('[AuthContext] Found patient data:', response.patient);
                setUser({
                    id: response.patient.id,
                    name: response.patient.name,
                    email: response.patient.email,
                    role: 'patient'
                });
            } else {
                console.log('[AuthContext] No patient data in response');
                setUser(null);
            }
        } catch (err) {
            console.log('[AuthContext] Not authenticated (expected if not logged in)');
            // User is not logged in, which is fine
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    const login = async (email, password) => {
        try {
            console.log('[AuthContext] Starting login for:', email);
            setLoading(true);
            setError(null);

            // Use the new JSON API for login
            const response = await djangoAPI.patient.login(email, password);
            console.log('[AuthContext] Login API response:', response);

            if (response?.success) {
                // Login successful, update user state from response
                if (response.patient) {
                    setUser({
                        id: response.patient.id,
                        name: response.patient.name,
                        email: response.patient.email,
                        role: 'patient'
                    });
                } else {
                    // Fetch user data if not in response
                    await checkAuthStatus();
                }
                return { success: true };
            } else {
                throw new Error(response?.error || 'Login failed');
            }
        } catch (err) {
            console.error('[AuthContext] Login error:', err);
            setError(err.message || 'Login failed');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const logout = async () => {
        try {
            setLoading(true);
            await djangoAPI.patient.logout();
            setUser(null);
            return { success: true };
        } catch (err) {
            console.error('[AuthContext] Logout error:', err);
            setError(err.message || 'Logout failed');
            // Still clear user on logout even if request fails
            setUser(null);
            return { success: false, error: err.message };
        } finally {
            setLoading(false);
        }
    };

    const value = {
        user,
        loading,
        error,
        login,
        logout,
        isAuthenticated: !!user,
        checkAuthStatus,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
