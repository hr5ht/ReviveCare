import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, LogIn, Heart, AlertCircle, Lock } from 'lucide-react';
import { Card, Button, FormInput } from '../components';
import { useAuth } from '../context/AuthContext';

export default function PatientLogin() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [dbStatus, setDbStatus] = useState({ ok: true, error: null });
    const navigate = useNavigate();
    const { login } = useAuth();

    // Check database health on mount
    React.useEffect(() => {
        const checkHealth = async () => {
            try {
                const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/health/`);
                const data = await response.json();
                if (!data.db_connected) {
                    setDbStatus({ ok: false, error: data.db_error || 'Database connection failed' });
                }
            } catch (err) {
                // If the whole backend is down, we handle that elsewhere or just let it fail at login
                console.error('Health check failed:', err);
            }
        };
        checkHealth();
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (dbStatus.ok === false) {
            setError(`Cannot login: Database is disconnected. (${dbStatus.error})`);
            return;
        }

        if (!email.trim()) {
            setError('Please enter your email address');
            return;
        }

        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            setError('Please enter a valid email address');
            return;
        }

        if (!password.trim()) {
            setError('Please enter your password');
            return;
        }

        setLoading(true);
        setError('');

        try {
            console.log('Attempting login with email:', email);
            const result = await login(email, password);
            console.log('Login result:', result);

            if (result.success) {
                console.log('Login successful, redirecting to dashboard');
                navigate('/patient/dashboard');
            } else {
                setError(result.error || 'Login failed. Please check your email or contact your doctor.');
            }
        } catch (err) {
            console.error('Login error caught:', err);
            if (err.message?.toLowerCase().includes('database') || err.message?.toLowerCase().includes('connection')) {
                setError('Database connection error. Please verify your NeonDB configuration.');
            } else {
                setError(err.message || 'Login failed. Please check your email or contact your doctor.');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-blue-50">
            {/* Header */}
            <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200 shadow-sm">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg">
                            <Heart className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-gray-900">ReviveCare</h1>
                            <p className="text-xs text-gray-600">Patient Portal</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Login Form */}
            <div className="flex items-center justify-center px-6 py-12">
                <Card className="w-full max-w-md">
                    <div className="text-center mb-8">
                        <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
                            <LogIn className="w-8 h-8 text-white" />
                        </div>
                        <h2 className="text-2xl font-bold text-gray-900 mb-2">Patient Login</h2>
                        <p className="text-gray-600">Enter your credentials to access your recovery dashboard</p>
                    </div>

                    {!dbStatus.ok && (
                        <div className="mb-6 p-4 bg-orange-50 border border-orange-200 rounded-xl flex items-start gap-3 shadow-sm animate-pulse">
                            <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center flex-shrink-0">
                                <AlertCircle className="w-6 h-6 text-orange-600" />
                            </div>
                            <div>
                                <h3 className="font-bold text-orange-800 text-sm mb-1">Database Disconnected</h3>
                                <p className="text-xs text-orange-700 leading-relaxed">
                                    The backend cannot reach NeonDB. Please check your <code className="bg-orange-100 px-1 rounded text-orange-900">DATABASE_URL</code> in Railway/Env.
                                </p>
                            </div>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <FormInput
                            label="Email Address"
                            type="email"
                            name="email"
                            placeholder="your.email@example.com"
                            icon={Mail}
                            value={email}
                            onChange={(e) => {
                                setEmail(e.target.value);
                                setError(''); // Clear error on input
                            }}
                            required
                        />

                        <FormInput
                            label="Password"
                            type="password"
                            name="password"
                            placeholder="Enter your password"
                            icon={Lock}
                            value={password}
                            onChange={(e) => {
                                setPassword(e.target.value);
                                setError(''); // Clear error on input
                            }}
                            required
                        />

                        {error && (
                            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-2">
                                <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
                                <p className="text-sm text-rose-700">{error}</p>
                            </div>
                        )}

                        <Button
                            type="submit"
                            variant="primary"
                            size="lg"
                            className="w-full"
                            icon={LogIn}
                            iconPosition="left"
                            disabled={loading}
                        >
                            {loading ? 'Logging in...' : 'Access Dashboard'}
                        </Button>

                        <div className="text-center">
                            <p className="text-sm text-gray-600">
                                Don't have access yet?{' '}
                                <button
                                    type="button"
                                    onClick={() => navigate('/')}
                                    className="text-emerald-600 hover:text-emerald-700 font-medium"
                                >
                                    Contact your doctor
                                </button>
                            </p>
                        </div>
                    </form>

                    {/* Info Card */}
                    <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <div className="flex items-start gap-3">
                            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                                <AlertCircle className="w-5 h-5 text-blue-600" />
                            </div>
                            <div>
                                <h3 className="font-semibold text-gray-900 text-sm mb-1">First Time Here?</h3>
                                <p className="text-sm text-gray-700 leading-relaxed">
                                    Your doctor will provide you with the email address used for your recovery plan.
                                    Use that email to log in and access your personalized dashboard.
                                </p>
                            </div>
                        </div>
                    </div>
                </Card>
            </div>
        </div>
    );
}
