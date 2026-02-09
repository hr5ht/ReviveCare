import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar, Users, FileText, Clock, Activity, Heart, Pill, AlertCircle, Bell, Search, Plus, ChevronRight, TrendingUp } from 'lucide-react';
import { Card, StatCard, Button } from '../components';

export default function MedicalDashboard() {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState('overview');

    const stats = [
        {
            icon: Users,
            label: 'Total Patients',
            value: '1,429',
            change: '+12%',
            trend: 'up',
            color: 'emerald'
        },
        {
            icon: Calendar,
            label: 'Appointments Today',
            value: '24',
            change: '3 pending',
            trend: 'neutral',
            color: 'blue'
        },
        {
            icon: Activity,
            label: 'Active Cases',
            value: '89',
            change: '-5% from last week',
            trend: 'neutral',
            color: 'purple'
        },
        {
            icon: Heart,
            label: 'Critical Alerts',
            value: '3',
            change: 'Require attention',
            trend: 'alert',
            color: 'rose'
        },
    ];

    const upcomingAppointments = [
        { id: 1, patient: 'Sarah Mitchell', time: '09:00 AM', type: 'Consultation', status: 'confirmed' },
        { id: 2, patient: 'James Wilson', time: '10:30 AM', type: 'Follow-up', status: 'confirmed' },
        { id: 3, patient: 'Emily Davis', time: '11:15 AM', type: 'Check-up', status: 'pending' },
        { id: 4, patient: 'Michael Chen', time: '02:00 PM', type: 'Consultation', status: 'confirmed' },
        { id: 5, patient: 'Lisa Anderson', time: '03:30 PM', type: 'Lab Review', status: 'pending' },
    ];

    const recentActivity = [
        { id: 1, action: 'Lab results uploaded', patient: 'John Thompson', time: '15 min ago', icon: FileText },
        { id: 2, action: 'New prescription added', patient: 'Maria Garcia', time: '32 min ago', icon: Pill },
        { id: 3, action: 'Appointment rescheduled', patient: 'Robert Lee', time: '1 hour ago', icon: Calendar },
        { id: 4, action: 'Vital signs updated', patient: 'Anna Smith', time: '2 hours ago', icon: Activity },
    ];

    const criticalAlerts = [
        { id: 1, message: 'Patient Sarah Mitchell - Blood pressure spike detected', severity: 'high', time: '5 min ago' },
        { id: 2, message: 'Lab results require immediate review - John Thompson', severity: 'medium', time: '23 min ago' },
        { id: 3, message: 'Medication refill needed - Emily Davis', severity: 'low', time: '1 hour ago' },
    ];

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-emerald-50/30">
            {/* Header */}
            <header className="bg-white/95 border-b border-slate-200 sticky top-0 z-50 backdrop-blur-sm">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/20">
                                <Heart className="w-6 h-6 text-white" fill="white" />
                            </div>
                            <div>
                                <h1 className="text-xl font-semibold text-slate-800 tracking-tight">HealthCare Portal</h1>
                                <p className="text-sm text-slate-500">Welcome back, Dr. Anderson</p>
                            </div>
                        </div>

                        <div className="flex items-center gap-4">
                            <div className="relative">
                                <Search className="w-5 h-5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                                <input
                                    type="text"
                                    placeholder="Search patients, records..."
                                    className="pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400 transition-all w-64"
                                />
                            </div>

                            <button className="relative p-2.5 hover:bg-slate-50 rounded-xl transition-colors">
                                <Bell className="w-5 h-5 text-slate-600" />
                                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-rose-500 rounded-full ring-2 ring-white"></span>
                            </button>

                            <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 to-emerald-500 rounded-xl flex items-center justify-center text-white font-medium shadow-sm">
                                DA
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            <div className="max-w-7xl mx-auto px-6 py-8">
                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
                    {stats.map((stat, index) => (
                        <StatCard
                            key={index}
                            icon={stat.icon}
                            label={stat.label}
                            value={stat.value}
                            change={stat.change}
                            trend={stat.trend}
                            color={stat.color}
                            style={{ animationDelay: `${index * 100}ms` }}
                        />
                    ))}
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Main Content Area */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Critical Alerts */}
                        {criticalAlerts.length > 0 && (
                            <Card padding="none" className="overflow-hidden">
                                <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-rose-50 to-white">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 bg-rose-100 rounded-lg flex items-center justify-center">
                                                <AlertCircle className="w-5 h-5 text-rose-600" />
                                            </div>
                                            <h2 className="text-lg font-semibold text-slate-800">Critical Alerts</h2>
                                        </div>
                                        <button className="text-sm text-rose-600 hover:text-rose-700 font-medium">
                                            View all
                                        </button>
                                    </div>
                                </div>
                                <div className="divide-y divide-slate-100">
                                    {criticalAlerts.map((alert) => (
                                        <div
                                            key={alert.id}
                                            className="px-6 py-4 hover:bg-slate-50/50 transition-colors cursor-pointer"
                                        >
                                            <div className="flex items-start justify-between gap-4">
                                                <div className="flex-1">
                                                    <p className="text-sm text-slate-700 mb-1">{alert.message}</p>
                                                    <p className="text-xs text-slate-400">{alert.time}</p>
                                                </div>
                                                <span className={`text-xs font-medium px-2.5 py-1 rounded-lg whitespace-nowrap ${alert.severity === 'high' ? 'bg-rose-100 text-rose-700' :
                                                    alert.severity === 'medium' ? 'bg-amber-100 text-amber-700' :
                                                        'bg-slate-100 text-slate-600'
                                                    }`}>
                                                    {alert.severity}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </Card>
                        )}

                        {/* Upcoming Appointments */}
                        <Card padding="none" className="overflow-hidden">
                            <div className="px-6 py-4 border-b border-slate-100">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                                            <Calendar className="w-5 h-5 text-blue-600" />
                                        </div>
                                        <h2 className="text-lg font-semibold text-slate-800">Today's Appointments</h2>
                                    </div>
                                    <Button variant="primary" size="sm" icon={Plus} iconPosition="left">
                                        New
                                    </Button>
                                </div>
                            </div>
                            <div className="divide-y divide-slate-100">
                                {upcomingAppointments.map((apt) => (
                                    <div
                                        key={apt.id}
                                        className="px-6 py-4 hover:bg-slate-50/50 transition-colors cursor-pointer group"
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-4">
                                                <div className="w-10 h-10 bg-gradient-to-br from-slate-100 to-slate-200 rounded-xl flex items-center justify-center text-slate-700 font-medium text-sm">
                                                    {apt.patient.split(' ').map(n => n[0]).join('')}
                                                </div>
                                                <div>
                                                    <p className="font-medium text-slate-800 mb-0.5">{apt.patient}</p>
                                                    <div className="flex items-center gap-3 text-sm text-slate-500">
                                                        <span className="flex items-center gap-1">
                                                            <Clock className="w-3.5 h-3.5" />
                                                            {apt.time}
                                                        </span>
                                                        <span className="text-slate-300">•</span>
                                                        <span>{apt.type}</span>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                <span className={`text-xs font-medium px-3 py-1.5 rounded-lg ${apt.status === 'confirmed'
                                                    ? 'bg-emerald-50 text-emerald-700'
                                                    : 'bg-amber-50 text-amber-700'
                                                    }`}>
                                                    {apt.status}
                                                </span>
                                                <ChevronRight className="w-5 h-5 text-slate-300 group-hover:text-slate-500 transition-colors" />
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </Card>
                    </div>

                    {/* Sidebar */}
                    <div className="space-y-6">
                        {/* Quick Actions */}
                        <Card>
                            <h3 className="text-base font-semibold text-slate-800 mb-4">Quick Actions</h3>
                            <div className="space-y-2">
                                <Button
                                    variant="primary"
                                    size="md"
                                    icon={Plus}
                                    iconPosition="left"
                                    className="w-full"
                                    onClick={() => navigate('/doctor/add-patient')}
                                >
                                    New Patient Record
                                </Button>
                                <Button
                                    variant="outline"
                                    size="md"
                                    icon={FileText}
                                    iconPosition="left"
                                    className="w-full"
                                    onClick={() => console.log('Generate Report - Coming soon')}
                                >
                                    Generate Report
                                </Button>
                                <button
                                    onClick={() => console.log('Prescribe Medication - Coming soon')}
                                    className="w-full px-4 py-3 bg-purple-50 hover:bg-purple-100 text-purple-700 rounded-xl text-sm font-medium transition-colors flex items-center justify-center gap-2"
                                >
                                    <Pill className="w-4 h-4" />
                                    Prescribe Medication
                                </button>
                            </div>
                        </Card>

                        {/* Recent Activity */}
                        <Card padding="none" className="overflow-hidden">
                            <div className="px-6 py-4 border-b border-slate-100">
                                <h3 className="text-base font-semibold text-slate-800">Recent Activity</h3>
                            </div>
                            <div className="px-6 py-4 space-y-4">
                                {recentActivity.map((activity) => {
                                    const Icon = activity.icon;
                                    return (
                                        <div key={activity.id} className="flex items-start gap-3">
                                            <div className="w-8 h-8 bg-slate-100 rounded-lg flex items-center justify-center flex-shrink-0">
                                                <Icon className="w-4 h-4 text-slate-600" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm text-slate-700 font-medium mb-0.5">{activity.action}</p>
                                                <p className="text-xs text-slate-500">{activity.patient}</p>
                                                <p className="text-xs text-slate-400 mt-1">{activity.time}</p>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </Card>

                        {/* Performance Card */}
                        <div className="bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-2xl p-6 text-white shadow-lg shadow-emerald-500/20">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
                                    <TrendingUp className="w-6 h-6 text-white" />
                                </div>
                                <h3 className="text-lg font-semibold">Performance</h3>
                            </div>
                            <div className="space-y-3">
                                <div>
                                    <div className="flex justify-between text-sm mb-1.5">
                                        <span className="text-emerald-50">Patient Satisfaction</span>
                                        <span className="font-semibold">94%</span>
                                    </div>
                                    <div className="w-full h-2 bg-white/20 rounded-full overflow-hidden">
                                        <div className="h-full bg-white rounded-full" style={{ width: '94%' }}></div>
                                    </div>
                                </div>
                                <div>
                                    <div className="flex justify-between text-sm mb-1.5">
                                        <span className="text-emerald-50">Appointments On-Time</span>
                                        <span className="font-semibold">87%</span>
                                    </div>
                                    <div className="w-full h-2 bg-white/20 rounded-full overflow-hidden">
                                        <div className="h-full bg-white rounded-full" style={{ width: '87%' }}></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}