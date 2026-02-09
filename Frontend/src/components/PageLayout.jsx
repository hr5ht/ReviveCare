import React from 'react';
import { Heart, Phone, Mail, MapPin } from 'lucide-react';

export const PageLayout = ({ children, showFooter = true }) => {
    return (
        <div className="min-h-screen bg-white">
            {children}

            {showFooter && (
                <footer className="bg-slate-900 text-white py-16">
                    <div className="max-w-7xl mx-auto px-6">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
                            {/* Brand */}
                            <div className="md:col-span-2">
                                <div className="flex items-center gap-3 mb-4">
                                    <div className="w-10 h-10 bg-linear-to-br from-emerald-500 to-emerald-600 rounded-xl flex items-center justify-center">
                                        <Heart className="w-6 h-6 text-white" fill="white" />
                                    </div>
                                    <span className="text-xl font-bold">ReViveCare</span>
                                </div>
                                <p className="text-slate-400 leading-relaxed mb-6">
                                    Empowering better health outcomes through innovative post-discharge recovery solutions.
                                </p>
                                <div className="space-y-3">
                                    <div className="flex items-center gap-3 text-slate-400">
                                        <Phone className="w-5 h-5 text-emerald-400" />
                                        <span>1-800-REVIVE-1</span>
                                    </div>
                                    <div className="flex items-center gap-3 text-slate-400">
                                        <Mail className="w-5 h-5 text-emerald-400" />
                                        <span>support@revivecare.com</span>
                                    </div>
                                    <div className="flex items-center gap-3 text-slate-400">
                                        <MapPin className="w-5 h-5 text-emerald-400" />
                                        <span>San Francisco, CA</span>
                                    </div>
                                </div>
                            </div>

                            {/* Links */}
                            <div>
                                <h4 className="font-semibold mb-4">Platform</h4>
                                <ul className="space-y-3 text-slate-400">
                                    <li><a href="#" className="hover:text-white transition-colors">Patient Portal</a></li>
                                    <li><a href="#" className="hover:text-white transition-colors">Doctor Portal</a></li>
                                    <li><a href="#" className="hover:text-white transition-colors">Features</a></li>
                                    <li><a href="#" className="hover:text-white transition-colors">Pricing</a></li>
                                </ul>
                            </div>

                            <div>
                                <h4 className="font-semibold mb-4">Company</h4>
                                <ul className="space-y-3 text-slate-400">
                                    <li><a href="#" className="hover:text-white transition-colors">About Us</a></li>
                                    <li><a href="#" className="hover:text-white transition-colors">Careers</a></li>
                                    <li><a href="#" className="hover:text-white transition-colors">Privacy Policy</a></li>
                                    <li><a href="#" className="hover:text-white transition-colors">Terms of Service</a></li>
                                </ul>
                            </div>
                        </div>

                        <div className="pt-8 border-t border-slate-800 text-center text-slate-400 text-sm">
                            <p>© 2024 ReViveCare. All rights reserved. HIPAA Compliant Healthcare Platform.</p>
                        </div>
                    </div>
                </footer>
            )}
        </div>
    );
};