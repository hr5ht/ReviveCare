import React from 'react';

export const WelcomeSection = ({
    title = 'Welcome back, Doctor',
    subtitle = 'Manage your patients\' recovery journey with ease',
    className = ''
}) => {
    return (
        <div className={`mb-8 ${className}`}>
            <h1 className="text-4xl font-bold text-slate-900 mb-2">
                {title}
            </h1>
            <p className="text-lg text-slate-600">
                {subtitle}
            </p>
        </div>
    );
};