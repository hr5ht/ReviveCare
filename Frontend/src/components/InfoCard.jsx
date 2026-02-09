import React from 'react';
import { Button } from './Button.jsx';

export const InfoCard = ({
    icon: Icon,
    title,
    description,
    buttonText,
    buttonColor = 'emerald',
    onButtonClick,
    className = ''
}) => {
    const colorClasses = {
        emerald: {
            iconBg: 'bg-emerald-100',
            iconText: 'text-emerald-600',
            button: 'primary'
        },
        blue: {
            iconBg: 'bg-blue-100',
            iconText: 'text-blue-600',
            button: 'outline'
        },
        purple: {
            iconBg: 'bg-purple-100',
            iconText: 'text-purple-600',
            button: 'outline'
        },
        rose: {
            iconBg: 'bg-rose-100',
            iconText: 'text-rose-600',
            button: 'outline'
        }
    };

    const colors = colorClasses[buttonColor];

    // Custom button styles for blue variant
    const customButtonClass = buttonColor === 'blue'
        ? 'bg-blue-50 hover:bg-blue-100 text-blue-700 border-blue-200'
        : '';

    return (
        <div className={`bg-white rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all duration-300 p-8 ${className}`}>
            <div className="flex flex-col h-full">
                {/* Icon */}
                <div className={`w-16 h-16 ${colors.iconBg} rounded-2xl flex items-center justify-center mb-6`}>
                    <Icon className={`w-8 h-8 ${colors.iconText}`} />
                </div>

                {/* Content */}
                <div className="flex-1 mb-6">
                    <h3 className="text-2xl font-bold text-slate-900 mb-3">
                        {title}
                    </h3>
                    <p className="text-slate-600 leading-relaxed">
                        {description}
                    </p>
                </div>

                {/* Button */}
                {buttonText && (
                    <Button
                        variant={colors.button}
                        size="md"
                        onClick={onButtonClick}
                        className={`w-full ${customButtonClass}`}
                    >
                        {buttonText}
                    </Button>
                )}
            </div>
        </div>
    );
};