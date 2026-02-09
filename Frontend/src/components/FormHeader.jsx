import React from 'react';

export const FormHeader = ({
    icon: Icon,
    title,
    subtitle,
    iconColor = 'emerald',
    className = ''
}) => {
    const colorClasses = {
        emerald: 'bg-emerald-100 text-emerald-600',
        blue: 'bg-blue-100 text-blue-600',
        purple: 'bg-purple-100 text-purple-600',
        rose: 'bg-rose-100 text-rose-600'
    };

    return (
        <div className={`text-center mb-8 ${className}`}>
            <div className="flex justify-center mb-4">
                <div className={`w-16 h-16 ${colorClasses[iconColor]} rounded-2xl flex items-center justify-center`}>
                    <Icon className="w-8 h-8" />
                </div>
            </div>
            <h2 className="text-2xl font-bold text-slate-900 mb-2">
                {title}
            </h2>
            {subtitle && (
                <p className="text-slate-600 leading-relaxed max-w-md mx-auto">
                    {subtitle}
                </p>
            )}
        </div>
    );
};