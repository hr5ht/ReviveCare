import React from 'react';

export const StatCard = ({
    icon: Icon,
    label,
    value,
    change,
    trend = 'neutral',
    color = 'emerald',
    className = '',
    ...props
}) => {
    const colorClasses = {
        emerald: 'bg-emerald-50 text-emerald-600',
        blue: 'bg-blue-50 text-blue-600',
        purple: 'bg-purple-50 text-purple-600',
        rose: 'bg-rose-50 text-rose-600',
        amber: 'bg-amber-50 text-amber-600'
    };

    const trendBadges = {
        up: 'text-emerald-600 bg-emerald-50',
        down: 'text-rose-600 bg-rose-50',
        alert: 'text-rose-600 bg-rose-50',
        neutral: 'text-slate-600 bg-slate-50'
    };

    return (
        <div
            className={`group bg-white rounded-2xl p-6 border border-slate-200 shadow-sm hover:shadow-md transition-all duration-300 ${className}`}
            {...props}
        >
            <div className="flex items-start justify-between mb-4">
                <div className={`w-12 h-12 ${colorClasses[color]} rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}>
                    <Icon className="w-6 h-6" />
                </div>
                {change && trend !== 'neutral' && (
                    <span className={`text-xs font-medium px-2 py-1 rounded-lg ${trendBadges[trend]}`}>
                        {change}
                    </span>
                )}
            </div>
            <div>
                <p className="text-sm text-slate-500 mb-1">{label}</p>
                <p className="text-3xl font-bold text-slate-800">{value}</p>
                {change && trend === 'neutral' && (
                    <p className="text-xs text-slate-400 mt-1">{change}</p>
                )}
            </div>
        </div>
    );
};