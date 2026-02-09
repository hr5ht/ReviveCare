import React from 'react';

export const FormInput = ({
    label,
    type = 'text',
    placeholder,
    icon: Icon,
    required = false,
    error,
    value,
    onChange,
    className = '',
    ...props
}) => {
    return (
        <div className={`mb-5 ${className}`}>
            {label && (
                <label className="block text-sm font-medium text-slate-700 mb-2">
                    {label}
                    {required && <span className="text-rose-500 ml-1">*</span>}
                </label>
            )}
            <div className="relative">
                {Icon && (
                    <div className="absolute left-3 top-1/2 -translate-y-1/2">
                        <Icon className="w-5 h-5 text-slate-400" />
                    </div>
                )}
                <input
                    type={type}
                    placeholder={placeholder}
                    value={value}
                    onChange={onChange}
                    className={`w-full ${Icon ? 'pl-11' : 'pl-4'} pr-4 py-3 bg-white border ${error ? 'border-rose-300 focus:border-rose-500 focus:ring-rose-500/20' : 'border-slate-200 focus:border-emerald-400 focus:ring-emerald-500/20'
                        } rounded-xl text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-4 transition-all`}
                    {...props}
                />
            </div>
            {error && (
                <p className="mt-1.5 text-sm text-rose-600">{error}</p>
            )}
        </div>
    );
};