import React from 'react';

export const ActionCard = ({
    icon: Icon,
    title,
    description,
    color = 'emerald',
    onClick,
    className = ''
}) => {
    const colorClasses = {
        emerald: {
            bg: 'bg-emerald-50',
            icon: 'text-emerald-600',
            hover: 'hover:bg-emerald-100',
            titleHover: 'group-hover:text-emerald-600'
        },
        blue: {
            bg: 'bg-blue-50',
            icon: 'text-blue-600',
            hover: 'hover:bg-blue-100',
            titleHover: 'group-hover:text-blue-600'
        },
        purple: {
            bg: 'bg-purple-50',
            icon: 'text-purple-600',
            hover: 'hover:bg-purple-100',
            titleHover: 'group-hover:text-purple-600'
        },
        rose: {
            bg: 'bg-rose-50',
            icon: 'text-rose-600',
            hover: 'hover:bg-rose-100',
            titleHover: 'group-hover:text-rose-600'
        }
    };

    const colors = colorClasses[color];

    return (
        <div
            onClick={onClick}
            className={`group bg-white rounded-2xl border border-slate-200 shadow-sm hover:shadow-xl transition-all duration-300 cursor-pointer p-8 ${className}`}
        >
            <div className="flex items-start gap-5">
                <div className={`w-16 h-16 ${colors.bg} rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}>
                    <Icon className={`w-8 h-8 ${colors.icon}`} />
                </div>
                <div className="flex-1">
                    <h3 className={`text-xl font-semibold text-slate-900 mb-2 ${colors.titleHover} transition-colors`}>
                        {title}
                    </h3>
                    <p className="text-slate-600 leading-relaxed">
                        {description}
                    </p>
                </div>
            </div>
        </div>
    );
};