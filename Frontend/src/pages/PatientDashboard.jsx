import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Heart, Dumbbell, MessageSquare, Calendar, TrendingUp, Clock, CheckCircle2, Target, Activity } from 'lucide-react';
import { Card, InfoCard, WelcomeSection } from '../components';
import { usePatientData } from '../hooks/usePatientData';

export default function PatientDashboard() {
    const navigate = useNavigate();
    const { patient, loading, error } = usePatientData();

    const handleStartExercises = () => {
        console.log('Start Exercises clicked');
        // TODO: Add navigation when exercises page is ready
        // navigate('/patient/exercises');
    };

    const handleStartChat = () => {
        console.log('Start Chat clicked');
        navigate('/patient/chat');
    };

    // Show loading state
    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-emerald-50/20 flex items-center justify-center">
                <div className="text-center">
                    <div className="w-16 h-16 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-slate-600">Loading your dashboard...</p>
                </div>
            </div>
        );
    }

    // Show error state
    if (error || !patient) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-emerald-50/20 flex items-center justify-center">
                <Card className="max-w-md">
                    <div className="text-center">
                        <div className="w-16 h-16 bg-rose-100 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Heart className="w-8 h-8 text-rose-600" />
                        </div>
                        <h2 className="text-xl font-bold text-slate-900 mb-2">Unable to Load Dashboard</h2>
                        <p className="text-slate-600 mb-4">{error || 'Please log in to view your dashboard'}</p>
                        <button
                            onClick={() => navigate('/patient/login')}
                            className="px-6 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
                        >
                            Go to Login
                        </button>
                    </div>
                </Card>
            </div>
        );
    }

    const patientName = patient.name || 'Patient';

    // Mock data for now - can be extended later when backend provides this data
    const todaysTasks = [
        { id: 1, task: 'Morning stretching routine', completed: true, time: '8:00 AM' },
        { id: 2, task: 'Take prescribed medication', completed: true, time: '9:00 AM' },
        { id: 3, task: 'Afternoon breathing exercises', completed: false, time: '2:00 PM' },
        { id: 4, task: 'Evening walk (15 minutes)', completed: false, time: '5:00 PM' }
    ];

    const recoveryStats = [
        { label: 'Days in Recovery', value: '12', icon: Calendar, color: 'emerald' },
        { label: 'Progress Score', value: '87%', icon: TrendingUp, color: 'blue' },
        { label: 'Goals Achieved', value: '8/10', icon: Target, color: 'purple' }
    ];

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-emerald-50/20">
            {/* Simple Header Bar */}
            <div className="bg-white border-b border-slate-200 shadow-sm">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        <button
                            onClick={() => navigate('/')}
                            className="flex items-center gap-3 hover:opacity-80 transition-opacity cursor-pointer"
                        >
                            <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-sm">
                                <Heart className="w-6 h-6 text-white" fill="white" />
                            </div>
                            <span className="text-xl font-bold text-slate-800">ReViveCare</span>
                        </button>

                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-slate-100 to-slate-200 rounded-xl flex items-center justify-center text-slate-700 font-semibold">
                                {patientName.split(' ').map(n => n[0]).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-6 py-8">
                {/* Welcome Section */}
                <WelcomeSection
                    title={`Welcome back, ${patientName}`}
                    subtitle="Your personalized recovery support dashboard"
                />

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Main Content - Left Side */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Main Cards Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Exercises Card */}
                            <InfoCard
                                icon={Dumbbell}
                                title="Exercises"
                                description="Access your personalized exercise routines designed for your recovery journey. Follow guided videos and track your progress."
                                buttonText="Start Exercises"
                                buttonColor="emerald"
                                onButtonClick={() => navigate('/patient/exercises')}
                            />

                            {/* Chatbot Card */}
                            <InfoCard
                                icon={MessageSquare}
                                title="Chatbot"
                                description="Get instant answers to your recovery questions. Our AI assistant is available 24/7 to provide support and guidance."
                                buttonText="Start Chat"
                                buttonColor="blue"
                                onButtonClick={handleStartChat}
                            />
                        </div>

                        {/* Today's Tasks */}
                        <Card padding="lg">
                            <div className="flex items-center justify-between mb-6">
                                <h3 className="text-xl font-bold text-slate-900">Today's Tasks</h3>
                                <span className="text-sm text-slate-500">
                                    {todaysTasks.filter(t => t.completed).length} of {todaysTasks.length} completed
                                </span>
                            </div>

                            <div className="space-y-3">
                                {todaysTasks.map((task) => (
                                    <div
                                        key={task.id}
                                        className={`flex items-center gap-4 p-4 rounded-xl border transition-all ${task.completed
                                            ? 'bg-emerald-50 border-emerald-200'
                                            : 'bg-white border-slate-200 hover:border-slate-300'
                                            }`}
                                    >
                                        <div className={`w-6 h-6 rounded-lg flex items-center justify-center flex-shrink-0 ${task.completed ? 'bg-emerald-500' : 'bg-slate-200'
                                            }`}>
                                            {task.completed && <CheckCircle2 className="w-4 h-4 text-white" />}
                                        </div>

                                        <div className="flex-1">
                                            <p className={`font-medium ${task.completed ? 'text-slate-500 line-through' : 'text-slate-900'}`}>
                                                {task.task}
                                            </p>
                                        </div>

                                        <div className="flex items-center gap-1 text-sm text-slate-500">
                                            <Clock className="w-4 h-4" />
                                            <span>{task.time}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </Card>
                    </div>

                    {/* Summary Card - Right Side */}
                    <div className="space-y-6">
                        {/* Quick Actions */}
                        <Card padding="lg">
                            <h3 className="text-xl font-bold text-slate-900 mb-4">Quick Actions</h3>

                            <div className="grid grid-cols-2 gap-3">
                                <button
                                    onClick={() => navigate('/patient/exercises')}
                                    className="p-4 bg-gradient-to-br from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white rounded-xl transition-all hover:scale-105 shadow-lg flex flex-col items-center justify-center"
                                >
                                    <Activity className="w-6 h-6 mb-2" />
                                    <div className="text-sm font-semibold">Start Exercising</div>
                                </button>

                                <button
                                    onClick={() => navigate('/patient/chat')}
                                    className="p-4 bg-gradient-to-br from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white rounded-xl transition-all hover:scale-105 shadow-lg flex flex-col items-center justify-center"
                                >
                                    <MessageSquare className="w-6 h-6 mb-2" />
                                    <div className="text-sm font-semibold">Chat with AI</div>
                                </button>
                            </div>
                        </Card>

                        {/* Recovery Summary */}
                        <Card padding="lg">
                            <h3 className="text-xl font-bold text-slate-900 mb-6">Recovery Summary</h3>

                            <div className="space-y-4">
                                {recoveryStats.map((stat, index) => {
                                    const Icon = stat.icon;
                                    const colorClasses = {
                                        emerald: 'bg-emerald-100 text-emerald-600',
                                        blue: 'bg-blue-100 text-blue-600',
                                        purple: 'bg-purple-100 text-purple-600'
                                    };

                                    return (
                                        <div key={index} className="flex items-center justify-between p-4 bg-slate-50 rounded-xl">
                                            <div className="flex items-center gap-3">
                                                <div className={`w-10 h-10 ${colorClasses[stat.color]} rounded-lg flex items-center justify-center`}>
                                                    <Icon className="w-5 h-5" />
                                                </div>
                                                <span className="text-sm font-medium text-slate-700">{stat.label}</span>
                                            </div>
                                            <span className="text-xl font-bold text-slate-900">{stat.value}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        </Card>

                        {/* Upcoming Appointment */}
                        <Card padding="lg" className="bg-gradient-to-br from-emerald-500 to-emerald-600 text-white border-emerald-600">
                            <div className="flex items-start gap-3 mb-4">
                                <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                                    <Calendar className="w-5 h-5 text-white" />
                                </div>
                                <div className="flex-1">
                                    <h4 className="font-semibold mb-1">Next Appointment</h4>
                                    <p className="text-emerald-50 text-sm">Follow-up checkup with Dr. Anderson</p>
                                </div>
                            </div>

                            <div className="pt-4 border-t border-white/20">
                                <div className="flex items-center justify-between text-sm">
                                    <span className="text-emerald-50">Date & Time</span>
                                    <span className="font-semibold">Feb 15, 2024 at 10:00 AM</span>
                                </div>
                            </div>
                        </Card>

                        {/* Health Tip */}
                        <Card padding="lg" className="bg-blue-50 border-blue-200">
                            <div className="flex items-start gap-3">
                                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                                    <Activity className="w-5 h-5 text-blue-600" />
                                </div>
                                <div>
                                    <h4 className="font-semibold text-slate-900 mb-2 text-sm">Daily Health Tip</h4>
                                    <p className="text-sm text-slate-600 leading-relaxed">
                                        Remember to stay hydrated throughout the day. Aim for 8 glasses of water to support your recovery process.
                                    </p>
                                </div>
                            </div>
                        </Card>
                    </div>
                </div>
            </div>
        </div>
    );
}