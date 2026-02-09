import React, { useState } from 'react';
import { UserPlus, User, Mail, FileText, CheckCircle2 } from 'lucide-react';
import { Card, Button, FormInput, FormTextarea, FormHeader } from '../components';

export default function AddPatientFormStandalone() {
    const [formData, setFormData] = useState({
        patientName: '',
        email: '',
        patientInfo: ''
    });

    const [errors, setErrors] = useState({});
    const [isSubmitted, setIsSubmitted] = useState(false);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
        // Clear error when user starts typing
        if (errors[name]) {
            setErrors(prev => ({
                ...prev,
                [name]: ''
            }));
        }
    };

    const validateForm = () => {
        const newErrors = {};

        if (!formData.patientName.trim()) {
            newErrors.patientName = 'Patient name is required';
        }

        if (!formData.email.trim()) {
            newErrors.email = 'Email address is required';
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
            newErrors.email = 'Please enter a valid email address';
        }

        if (!formData.patientInfo.trim()) {
            newErrors.patientInfo = 'Patient information is required';
        }

        return newErrors;
    };

    const handleSubmit = (e) => {
        e.preventDefault();

        const newErrors = validateForm();

        if (Object.keys(newErrors).length > 0) {
            setErrors(newErrors);
            return;
        }

        // Simulate form submission
        console.log('Form submitted:', formData);
        setIsSubmitted(true);

        // Reset form after 2 seconds
        setTimeout(() => {
            setFormData({
                patientName: '',
                email: '',
                patientInfo: ''
            });
            setIsSubmitted(false);
        }, 2000);
    };

    return (
        <div className="min-h-screen bg-linear-to-br from-slate-50 via-white to-emerald-50/20 flex items-center justify-center p-6">
            {/* Centered Card Container */}
            <Card
                variant="elevated"
                padding="none"
                className="w-full max-w-2xl overflow-hidden"
            >
                {/* Form Header */}
                <div className="p-8 pb-6">
                    <FormHeader
                        icon={UserPlus}
                        title="Add Patient Information"
                        subtitle="Enter the patient's details to register them in the recovery program"
                        iconColor="emerald"
                    />
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="px-8 pb-8">
                    {/* Patient Name */}
                    <FormInput
                        label="Patient Name"
                        type="text"
                        name="patientName"
                        placeholder="Enter patient's full name"
                        icon={User}
                        required
                        value={formData.patientName}
                        onChange={handleChange}
                        error={errors.patientName}
                    />

                    {/* Email Address */}
                    <FormInput
                        label="Email Address"
                        type="email"
                        name="email"
                        placeholder="patient@example.com"
                        icon={Mail}
                        required
                        value={formData.email}
                        onChange={handleChange}
                        error={errors.email}
                    />

                    {/* Patient Information */}
                    <FormTextarea
                        label="Patient Information"
                        name="patientInfo"
                        placeholder="Enter medical history, current condition, recovery plan, and any relevant notes..."
                        icon={FileText}
                        required
                        rows={6}
                        value={formData.patientInfo}
                        onChange={handleChange}
                        error={errors.patientInfo}
                    />

                    {/* Submit Button */}
                    <Button
                        type="submit"
                        variant="primary"
                        size="lg"
                        className="w-full mt-2"
                        icon={isSubmitted ? CheckCircle2 : UserPlus}
                        iconPosition="left"
                    >
                        {isSubmitted ? 'Patient Added Successfully!' : 'Add Patient'}
                    </Button>

                    {/* Helper Text */}
                    <p className="text-center text-sm text-slate-500 mt-4">
                        All fields marked with <span className="text-rose-500">*</span> are required
                    </p>
                </form>

                {/* Information Footer */}
                <div className="bg-blue-50 border-t border-blue-100 p-6">
                    <div className="flex items-start gap-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flexs-0">
                            <FileText className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-slate-900 mb-1 text-sm">Patient Information Guidelines</h3>
                            <p className="text-sm text-slate-600 leading-relaxed">
                                Please include relevant medical history, current medications, allergies, emergency contacts,
                                and any specific care instructions for the patient's recovery journey.
                            </p>
                        </div>
                    </div>
                </div>
            </Card>
        </div>
    );
}