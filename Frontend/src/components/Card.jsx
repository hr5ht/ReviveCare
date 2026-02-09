import React from 'react';

export const Card = ({
    children,
    variant = 'default',
    padding = 'md',
    hover = true,
    className = '',
    ...props
}) => {
    const baseStyles = 'bg-white rounded-2xl border transition-all duration-300';

    const variants = {
        default: 'border-slate-200 shadow-sm',
        elevated: 'border-slate-200 shadow-lg shadow-slate-900/5',
        gradient: 'border-slate-200 bg-gradient-to-br from-slate-50 to-slate-100/50',
        feature: 'border-slate-200 hover:border-emerald-200 hover:shadow-lg hover:shadow-emerald-500/5',
    };

    const paddings = {
        none: '',
        sm: 'p-4',
        md: 'p-6',
        lg: 'p-8'
    };

    const hoverStyles = hover ? 'hover:shadow-md' : '';

    return (
        <div
            className={`${baseStyles} ${variants[variant]} ${paddings[padding]} ${hoverStyles} ${className}`}
            {...props}
        >
            {children}
        </div>
    );
};