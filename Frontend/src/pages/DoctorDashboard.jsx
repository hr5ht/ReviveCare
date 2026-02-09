import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Heart, Users, Bell, TrendingUp, FileText, UserPlus, ClipboardList, Calendar, Activity, Pill, Phone, Video, MessageSquare } from 'lucide-react';
import { Navbar, WelcomeSection, StatCard, ActionCard, Card, Button } from '../components';

export default function DoctorDashboard() {
    const navigate = useNavigate();
    const stats = [
        {
            icon: Users,
            label: 'Active Patients',
            value: '127',
            color: 'emerald'
        },
        {
            icon: Bell,
            label: 'New Alerts',
            value: '8',
            color: 'rose'
        },
        {
            icon: TrendingUp,
            label: 'Avg Progress Rate',
            value: '92%',
            color: 'blue'
        },
        {
            icon: FileText,
            label: 'Pending Reviews',
            value: '15',
            color: 'amber'
        }
    ];

    const quickActions = [
        { icon: Calendar, label: 'Schedule Appointment', color: 'purple' },
        { icon: Activity, label: 'Monitor Vitals', color: 'rose' },
        { icon: Pill, label: 'Prescribe Medication', color: 'emerald' },
        { icon: Video, label: 'Start Telehealth', color: 'blue' }
    ];

    const recentPatients = [
        { id: 1, name: 'Sarah Mitchell', condition: 'Post-Surgery Recovery', status: 'improving', lastUpdate: '2 hours ago' },
        { id: 2, name: 'James Wilson', condition: 'Cardiac Rehabilitation', status: 'stable', lastUpdate: '5 hours ago' },
        { id: 3, name: 'Emily Davis', condition: 'Physical Therapy', status: 'critical', lastUpdate: '30 min ago' },
        { id: 4, name: 'Michael Chen', condition: 'Medication Management', status: 'improving', lastUpdate: '1 day ago' }
    ];

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-emerald-50/20">
            {/* Top Navbar */}
            <Navbar
                doctorName="Dr. Anderson"
                specialty="Cardiologist"
                notificationCount={8}
                variant="green"
            />

            <div className="max-w-7xl mx-auto px-6 py-8">
                {/* Welcome Section */}
                <WelcomeSection
                    title="Welcome back, Doctor"
                    subtitle="Manage your patients' recovery journey with ease"
                />

                {/* Stats Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
                    {stats.map((stat, index) => (
                        <StatCard
                            key={index}
                            icon={stat.icon}
                            label={stat.label}
                            value={stat.value}
                            color={stat.color}
                        />
                    ))}
                </div>

                {/* Main Actions Section */}
                <div className="mb-8">
                    <h2 className="text-2xl font-bold text-slate-900 mb-5">Main Actions</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <ActionCard
                            icon={UserPlus}
                            title="Add Patient"
                            description="Register a new patient to the recovery program"
                            color="emerald"
                            onClick={() => navigate('/doctor/add-patient')}
                        />
                        <ActionCard
                            icon={ClipboardList}
                            title="View Reports"
                            description="Access patient recovery reports and analytics"
                            color="blue"
                            onClick={() => console.log('View Reports - Coming soon')}
                        />
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Quick Actions */}
                    <div className="lg:col-span-2">
                        <Card padding="lg">
                            <h3 className="text-xl font-semibold text-slate-900 mb-5">Quick Actions</h3>
                            <div className="grid grid-cols-2 gap-4">
                                {quickActions.map((action, index) => {
                                    const Icon = action.icon;
                                    const colorClasses = {
                                        emerald: 'bg-emerald-50 text-emerald-600 hover:bg-emerald-100',
                                        blue: 'bg-blue-50 text-blue-600 hover:bg-blue-100',
                                        purple: 'bg-purple-50 text-purple-600 hover:bg-purple-100',
                                        rose: 'bg-rose-50 text-rose-600 hover:bg-rose-100'
                                    };

                                    return (
                                        <button
                                            key={index}
                                            onClick={() => console.log(`${action.label} - Coming soon`)}
                                            className={`flex items-center gap-3 p-4 rounded-xl ${colorClasses[action.color]} transition-all duration-200 text-left`}
                                        >
                                            <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-sm">
                                                <Icon className="w-5 h-5" />
                                            </div>
                                            <span className="font-medium text-sm">{action.label}</span>
                                        </button>
                                    );
                                })}
                            </div>
                        </Card>

                        {/* Recent Patients */}
                        <Card padding="none" className="mt-6 overflow-hidden">
                            <div className="px-6 py-4 border-b border-slate-100">
                                <h3 className="text-xl font-semibold text-slate-900">Recent Patients</h3>
                            </div>
                            <div className="divide-y divide-slate-100">
                                {recentPatients.map((patient) => {
                                    const statusColors = {
                                        improving: 'bg-emerald-100 text-emerald-700',
                                        stable: 'bg-blue-100 text-blue-700',
                                        critical: 'bg-rose-100 text-rose-700'
                                    };

                                    return (
                                        <div
                                            key={patient.id}
                                            className="px-6 py-4 hover:bg-slate-50 transition-colors cursor-pointer"
                                        >
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-4">
                                                    <div className="w-12 h-12 bg-gradient-to-br from-slate-100 to-slate-200 rounded-xl flex items-center justify-center text-slate-700 font-semibold">
                                                        {patient.name.split(' ').map(n => n[0]).join('')}
                                                    </div>
                                                    <div>
                                                        <p className="font-semibold text-slate-900">{patient.name}</p>
                                                        <p className="text-sm text-slate-500">{patient.condition}</p>
                                                    </div>
                                                </div>
                                                <div className="text-right">
                                                    <span className={`text-xs font-medium px-3 py-1.5 rounded-lg ${statusColors[patient.status]}`}>
                                                        {patient.status}
                                                    </span>
                                                    <p className="text-xs text-slate-400 mt-1">{patient.lastUpdate}</p>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </Card>
                    </div>

                    {/* Sidebar - Today's Schedule */}
                    <div className="space-y-6">
                        <Card padding="lg">
                            <h3 className="text-lg font-semibold text-slate-900 mb-4">Today's Schedule</h3>
                            <div className="space-y-4">
                                <div className="flex items-start gap-3 p-3 bg-emerald-50 rounded-xl">
                                    <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center flex-shrink-0">
                                        <Calendar className="w-5 h-5 text-emerald-600" />
                                    </div>
                                    <div>
                                        <p className="font-medium text-slate-900 text-sm">Morning Rounds</p>
                                        <p className="text-xs text-slate-600">8:00 AM - 10:00 AM</p>
                                    </div>
                                </div>

                                <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-xl">
                                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                                        <Video className="w-5 h-5 text-blue-600" />
                                    </div>
                                    <div>
                                        <p className="font-medium text-slate-900 text-sm">Telehealth Sessions</p>
                                        <p className="text-xs text-slate-600">11:00 AM - 2:00 PM</p>
                                    </div>
                                </div>

                                <div className="flex items-start gap-3 p-3 bg-purple-50 rounded-xl">
                                    <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
                                        <FileText className="w-5 h-5 text-purple-600" />
                                    </div>
                                    <div>
                                        <p className="font-medium text-slate-900 text-sm">Review Reports</p>
                                        <p className="text-xs text-slate-600">3:00 PM - 4:00 PM</p>
                                    </div>
                                </div>
                            </div>
                        </Card>

                        {/* Contact Support */}
                        <Card padding="lg" className="bg-gradient-to-br from-slate-900 to-slate-800 text-white">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center">
                                    <Phone className="w-5 h-5 text-white" />
                                </div>
                                <h3 className="text-lg font-semibold">Need Help?</h3>
                            </div>
                            <p className="text-slate-300 text-sm mb-4">
                                Our support team is available 24/7 to assist you.
                            </p>
                            <Button variant="white" size="sm" className="w-full">
                                Contact Support
                            </Button>
                        </Card>
                    </div>
                </div>
            </div>
        </div>
    );
}