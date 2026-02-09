import React from 'react';
import { Heart, Bell } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Navbar = ({
    doctorName = 'Dr. Anderson',
    specialty = 'Cardiologist',
    notificationCount = 0,
    variant = 'green' // 'green' or 'white'
}) => {
    const navigate = useNavigate();

    const variantStyles = {
        green: {
            bg: 'bg-gradient-to-r from-emerald-500 to-emerald-600',
            shadow: 'shadow-lg shadow-emerald-500/20',
            text: 'text-white',
            logoRing: 'bg-white/20',
            profileBg: 'bg-white/10',
            bellHover: 'hover:bg-white/10'
        },
        white: {
            bg: 'bg-white border-b border-slate-200',
            shadow: 'shadow-sm',
            text: 'text-slate-800',
            logoRing: 'bg-emerald-100',
            profileBg: 'bg-slate-50',
            bellHover: 'hover:bg-slate-100'
        }
    };

    const styles = variantStyles[variant];

    return (
        <nav className={`${styles.bg} ${styles.shadow}`}>
            <div className="max-w-7xl mx-auto px-6 py-4">
                <div className="flex items-center justify-between">
                    {/* Left: Logo - Clickable to go Home */}
                    <button
                        onClick={() => navigate('/')}
                        className="flex items-center gap-3 hover:opacity-80 transition-opacity cursor-pointer"
                    >
                        <div className={`w-10 h-10 ${styles.logoRing} backdrop-blur-sm rounded-xl flex items-center justify-center`}>
                            <Heart
                                className={`w-6 h-6 ${variant === 'green' ? 'text-white' : 'text-emerald-600'}`}
                                fill={variant === 'green' ? 'white' : '#059669'}
                            />
                        </div>
                        <span className={`text-2xl font-bold ${styles.text} tracking-tight`}>
                            ReViveCare
                        </span>
                    </button>

                    {/* Right: Doctor Profile */}
                    <div className="flex items-center gap-4">
                        <button className={`relative p-2 ${styles.bellHover} rounded-lg transition-colors`}>
                            <Bell className={`w-5 h-5 ${styles.text}`} />
                            {notificationCount > 0 && (
                                <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-rose-500 rounded-full ring-2 ring-current"></span>
                            )}
                        </button>

                        <div className={`flex items-center gap-3 ${styles.profileBg} backdrop-blur-sm rounded-xl px-4 py-2`}>
                            <div className={`w-10 h-10 ${variant === 'green' ? 'bg-white' : 'bg-emerald-100'} rounded-lg flex items-center justify-center ${variant === 'green' ? 'text-emerald-600' : 'text-emerald-700'} font-semibold`}>
                                {doctorName.split(' ').map(n => n[0]).join('')}
                            </div>
                            <div className="text-left">
                                <p className={`${styles.text} font-semibold text-sm`}>
                                    {doctorName}
                                </p>
                                <p className={`${variant === 'green' ? 'text-emerald-100' : 'text-slate-500'} text-xs`}>
                                    {specialty}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </nav>
    );
};