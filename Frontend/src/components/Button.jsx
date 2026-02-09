import React from 'react';

export const Button = ({
    children,
    variant = 'primary',
    size = 'md',
    icon: Icon,
    iconPosition = 'left',
    className = '',
    ...props
}) => {
    const baseStyles = 'inline-flex items-center justify-center gap-3 font-semibold transition-all rounded-2xl';

    const variants = {
        primary: 'bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white shadow-lg shadow-emerald-500/30 hover:shadow-xl hover:shadow-emerald-500/40',
        secondary: 'bg-white hover:bg-slate-50 text-slate-800 shadow-lg shadow-slate-900/5 hover:shadow-xl hover:shadow-slate-900/10 border border-slate-200',
        outline: 'bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200',
        ghost: 'bg-transparent hover:bg-slate-50 text-slate-700',
        white: 'bg-white hover:bg-slate-50 text-emerald-600 shadow-xl shadow-emerald-900/20 hover:shadow-2xl hover:shadow-emerald-900/30'
    };

    const sizes = {
        sm: 'px-4 py-2 text-sm',
        md: 'px-6 py-3 text-base',
        lg: 'px-8 py-5 text-lg'
    };

    return (
        <button
            className={`group ${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
            {...props}
        >
            {Icon && iconPosition === 'left' && (
                <Icon className="w-5 h-5 group-hover:scale-110 transition-transform" />
            )}
            {children}
            {Icon && iconPosition === 'right' && (
                <Icon className="w-5 h-5 group-hover:translate-x-0.5 transition-all" />
            )}
        </button>
    );
};
