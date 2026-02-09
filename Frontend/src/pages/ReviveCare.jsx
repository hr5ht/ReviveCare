import React from 'react';
import { useNavigate } from 'react-router-dom';
import { UserCircle2, Stethoscope, Shield, Clock, Heart, TrendingUp, CheckCircle2, ArrowRight } from 'lucide-react';
import { Button, PageLayout, FeatureCard } from '../components';


export default function ReviveCare() {
    const navigate = useNavigate();
    const features = [
        {
            icon: Clock,
            title: 'Real-Time Monitoring',
            description: 'Track patient recovery progress with continuous health data monitoring and automated alerts.'
        },
        {
            icon: Heart,
            title: 'Personalized Care Plans',
            description: 'Customized recovery protocols tailored to each patient\'s specific medical needs and conditions.'
        },
        {
            icon: Shield,
            title: 'HIPAA Compliant',
            description: 'Enterprise-grade security ensuring patient data privacy and regulatory compliance.'
        },
        {
            icon: TrendingUp,
            title: 'Analytics Dashboard',
            description: 'Comprehensive insights into recovery trends, medication adherence, and health outcomes.'
        }
    ];

    const benefits = [
        'Reduce hospital readmission rates',
        'Improve patient satisfaction scores',
        'Streamline post-discharge communication',
        'Enable proactive intervention',
        'Comprehensive medication management',
        'Integrated telehealth consultations'
    ];

    return (
        <PageLayout>
            {/* Hero Section with Gradient Background */}
            <section className="relative overflow-hidden bg-gradient-to-br from-blue-50 via-purple-50/40 to-indigo-50/60">
                {/* Decorative Elements */}
                <div className="absolute top-0 left-0 w-96 h-96 bg-blue-400/10 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2"></div>
                <div className="absolute bottom-0 right-0 w-96 h-96 bg-purple-400/10 rounded-full blur-3xl translate-x-1/3 translate-y-1/3"></div>

                <div className="relative max-w-7xl mx-auto px-6 pt-20 pb-32 lg:pt-32 lg:pb-40">
                    <div className="text-center max-w-4xl mx-auto">
                        {/* Logo/Brand */}
                        <div className="flex items-center justify-center gap-3 mb-8">
                            <div className="w-14 h-14 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-2xl flex items-center justify-center shadow-lg shadow-emerald-500/30">
                                <Heart className="w-8 h-8 text-white" fill="white" />
                            </div>
                            <span className="text-2xl font-bold text-slate-800 tracking-tight">ReViveCare</span>
                        </div>

                        {/* Heading */}
                        <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-slate-900 mb-6 leading-tight tracking-tight">
                            Welcome to <span className="bg-gradient-to-r from-emerald-600 to-emerald-500 bg-clip-text text-transparent">ReViveCare</span>
                        </h1>

                        {/* Subheading */}
                        <p className="text-xl md:text-2xl text-slate-600 mb-12 leading-relaxed max-w-3xl mx-auto">
                            Comprehensive post-discharge recovery support platform connecting patients with their care teams for seamless healing and monitoring.
                        </p>

                        {/* CTA Buttons */}
                        <div className="flex flex-col sm:flex-row items-center justify-center gap-5 mb-16">
                            <button
                                onClick={() => navigate('/patient')}
                                className="group w-full sm:w-auto px-8 py-5 bg-white hover:bg-slate-50 text-slate-800 rounded-2xl text-lg font-semibold transition-all shadow-lg shadow-slate-900/5 hover:shadow-xl hover:shadow-slate-900/10 border border-slate-200 flex items-center justify-center gap-3 min-w-[240px]"
                            >
                                <div className="w-10 h-10 bg-slate-100 rounded-xl flex items-center justify-center group-hover:bg-slate-200 transition-colors">
                                    <UserCircle2 className="w-6 h-6 text-slate-700" />
                                </div>
                                <span>Patient Portal</span>
                                <ArrowRight className="w-5 h-5 text-slate-400 group-hover:text-slate-600 group-hover:translate-x-0.5 transition-all" />
                            </button>

                            <button
                                onClick={() => navigate('/doctor')}
                                className="group w-full sm:w-auto px-8 py-5 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white rounded-2xl text-lg font-semibold transition-all shadow-lg shadow-emerald-500/30 hover:shadow-xl hover:shadow-emerald-500/40 flex items-center justify-center gap-3 min-w-[240px]"
                            >
                                <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center group-hover:bg-white/30 transition-colors">
                                    <Stethoscope className="w-6 h-6 text-white" />
                                </div>
                                <span>Doctor Portal</span>
                                <ArrowRight className="w-5 h-5 group-hover:translate-x-0.5 transition-all" />
                            </button>
                        </div>

                        {/* Trust Indicators */}
                        <div className="flex flex-wrap items-center justify-center gap-8 text-sm text-slate-500">
                            <div className="flex items-center gap-2">
                                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                                <span>HIPAA Certified</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                                <span>24/7 Support</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                                <span>Trusted by 500+ Hospitals</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Wave Separator */}
                <div className="absolute bottom-0 left-0 right-0">
                    <svg className="w-full h-16 md:h-24" viewBox="0 0 1440 100" fill="none" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">
                        <path d="M0,50 C240,80 480,80 720,50 C960,20 1200,20 1440,50 L1440,100 L0,100 Z" fill="white" />
                    </svg>
                </div>
            </section>

            {/* Why ReViveCare Section */}
            <section className="py-20 lg:py-32 bg-white">
                <div className="max-w-7xl mx-auto px-6">
                    {/* Section Header */}
                    <div className="text-center mb-16 lg:mb-20">
                        <h2 className="text-4xl md:text-5xl font-bold text-slate-900 mb-5">
                            Why ReViveCare?
                        </h2>
                        <p className="text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed">
                            Our platform bridges the gap between hospital discharge and complete recovery, ensuring patients receive continuous, quality care at home.
                        </p>
                    </div>

                    {/* Features Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-20">
                        {features.map((feature, index) => (
                            <FeatureCard
                                key={index}
                                icon={feature.icon}
                                title={feature.title}
                                description={feature.description}
                            />
                        ))}
                    </div>

                    {/* Benefits Section */}
                    <div className="bg-gradient-to-br from-slate-50 to-slate-100/50 rounded-3xl p-10 lg:p-16 border border-slate-200">
                        <div className="grid md:grid-cols-2 gap-12 lg:gap-16 items-center">
                            <div>
                                <h3 className="text-3xl font-bold text-slate-900 mb-6">
                                    Transform Your Recovery Process
                                </h3>
                                <p className="text-lg text-slate-600 mb-8 leading-relaxed">
                                    ReViveCare empowers healthcare providers and patients with the tools needed for successful post-discharge outcomes.
                                </p>
                                <div className="grid grid-cols-1 gap-4">
                                    {benefits.map((benefit, index) => (
                                        <div key={index} className="flex items-start gap-3">
                                            <div className="w-6 h-6 bg-emerald-500 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                                                <CheckCircle2 className="w-4 h-4 text-white" />
                                            </div>
                                            <span className="text-slate-700 font-medium">{benefit}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="relative">
                                <div className="bg-white rounded-2xl p-8 shadow-xl shadow-slate-900/10 border border-slate-200">
                                    <div className="space-y-6">
                                        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                                            <span className="text-slate-600 font-medium">Patient Satisfaction</span>
                                            <span className="text-2xl font-bold text-emerald-600">98%</span>
                                        </div>
                                        <div>
                                            <div className="flex justify-between text-sm mb-3">
                                                <span className="text-slate-600">Recovery Tracking</span>
                                                <span className="text-slate-900 font-semibold">95%</span>
                                            </div>
                                            <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
                                                <div className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-full" style={{ width: '95%' }}></div>
                                            </div>
                                        </div>
                                        <div>
                                            <div className="flex justify-between text-sm mb-3">
                                                <span className="text-slate-600">Medication Adherence</span>
                                                <span className="text-slate-900 font-semibold">92%</span>
                                            </div>
                                            <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
                                                <div className="h-full bg-gradient-to-r from-blue-500 to-blue-400 rounded-full" style={{ width: '92%' }}></div>
                                            </div>
                                        </div>
                                        <div>
                                            <div className="flex justify-between text-sm mb-3">
                                                <span className="text-slate-600">Follow-up Completion</span>
                                                <span className="text-slate-900 font-semibold">88%</span>
                                            </div>
                                            <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
                                                <div className="h-full bg-gradient-to-r from-purple-500 to-purple-400 rounded-full" style={{ width: '88%' }}></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                {/* Decorative gradient blob */}
                                <div className="absolute -bottom-6 -right-6 w-32 h-32 bg-gradient-to-br from-emerald-400/20 to-blue-400/20 rounded-3xl blur-2xl -z-10"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-20 lg:py-24 bg-gradient-to-br from-emerald-500 to-emerald-600">
                <div className="max-w-5xl mx-auto px-6 text-center">
                    <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
                        Ready to Transform Patient Recovery?
                    </h2>
                    <p className="text-xl text-emerald-50 mb-10 leading-relaxed">
                        Join hundreds of healthcare providers delivering exceptional post-discharge care.
                    </p>
                    <Button variant="white" size="lg" icon={ArrowRight} iconPosition="right">
                        Schedule a Demo
                    </Button>
                </div>
            </section>
        </PageLayout>
    );
}