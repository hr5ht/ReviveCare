import React from 'react';

export const FeatureCard = ({
    icon: Icon,
    title,
    description,
    className = '',
    ...props
}) => {
    return (
        <div
            className={`group p-8 rounded-2xl border border-slate-200 hover:border-emerald-200 hover:shadow-lg hover:shadow-emerald-500/5 transition-all duration-300 bg-white ${className}`}
            {...props}
        >
            <div className="w-14 h-14 bg-linear-to-br from-emerald-50 to-emerald-100 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                <Icon className="w-7 h-7 text-emerald-600" />
            </div>
            <h3 className="text-xl font-semibold text-slate-800 mb-3">{title}</h3>
            <p className="text-slate-600 leading-relaxed">{description}</p>
        </div>
    );
};