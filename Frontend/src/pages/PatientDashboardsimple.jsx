import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Heart, Dumbbell, MessageSquare, X, Camera } from 'lucide-react';
import { InfoCard, WelcomeSection } from '../components';

export default function PatientDashboardSimple() {
    const navigate = useNavigate();
    const patientName = 'Sarah Mitchell';
    const [showCamera, setShowCamera] = useState(false);
    const [cameraStream, setCameraStream] = useState(null);
    const videoRef = useRef(null);

    const handleStartExercises = async () => {
        try {
            // Request camera access
            const stream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: false
            });

            setCameraStream(stream);
            setShowCamera(true);

            // Set the video element to display the stream
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
            }
        } catch (error) {
            console.error('Error accessing camera:', error);
            alert('Unable to access camera. Please make sure you have granted camera permissions.');
        }
    };

    const handleCloseCamera = () => {
        // Stop all video tracks
        if (cameraStream) {
            cameraStream.getTracks().forEach(track => track.stop());
            setCameraStream(null);
        }
        setShowCamera(false);
    };

    const handleStartChat = () => {
        console.log('Start Chat clicked');
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-emerald-50/20">
            {/* Simple Header Bar */}
            <div className="bg-white border-b border-slate-200 shadow-sm">
                <div className="max-w-6xl mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        <button
                            onClick={() => navigate('/')}
                            className="flex items-center gap-3 hover:opacity-80 transition-opacity cursor-pointer"
                        >
                            <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-sm">
                                <Heart className="w-6 h-6 text-white" fill="white" />
                            </div>
                            <span className="text-xl font-bold text-slate-800">ReViveCare</span>
                        </button>

                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-slate-100 to-slate-200 rounded-xl flex items-center justify-center text-slate-700 font-semibold text-sm">
                                {patientName.split(' ').map(n => n[0]).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-6xl mx-auto px-6 py-12">
                {/* Welcome Section */}
                <WelcomeSection
                    title={`Welcome back, ${patientName} `}
                    subtitle="Your personalized recovery support dashboard"
                />

                {/* Main Cards Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto">
                    {/* Exercises Card */}
                    <InfoCard
                        icon={Dumbbell}
                        title="Exercises"
                        description="Access your personalized exercise routines designed for your recovery journey. Follow guided videos and track your progress."
                        buttonText="Start Exercises"
                        buttonColor="emerald"
                        onButtonClick={handleStartExercises}

                    />

                    {/* Chatbot Card */}
                    <InfoCard
                        icon={MessageSquare}
                        title="Chatbot"
                        description="Get instant answers to your recovery questions. Our AI assistant is available 24/7 to provide support and guidance."
                        buttonText="Start Chat"
                        buttonColor="blue"
                        onButtonClick={handleStartChat}
                    />
                </div>

                {/* Camera Modal */}
                {showCamera && (
                    <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center">
                        <div className="relative w-full h-full max-w-6xl max-h-screen p-6">
                            {/* Close button */}
                            <button
                                onClick={handleCloseCamera}
                                className="absolute top-8 right-8 z-10 w-12 h-12 bg-rose-500 hover:bg-rose-600 rounded-full flex items-center justify-center text-white transition-colors shadow-lg"
                            >
                                <X className="w-6 h-6" />
                            </button>

                            {/* Camera info banner */}
                            <div className="absolute top-8 left-8 z-10 bg-emerald-500 text-white px-6 py-3 rounded-xl shadow-lg flex items-center gap-3">
                                <Camera className="w-5 h-5" />
                                <span className="font-semibold">Exercise Camera Active</span>
                            </div>

                            {/* Video element */}
                            <div className="w-full h-full flex items-center justify-center">
                                <video
                                    ref={videoRef}
                                    autoPlay
                                    playsInline
                                    className="max-w-full max-h-full rounded-2xl shadow-2xl"
                                />
                            </div>

                            {/* Instructions */}
                            <div className="absolute bottom-8 left-1/2 -translate-x-1/2 bg-white/10 backdrop-blur-sm text-white px-6 py-4 rounded-xl text-center">
                                <p className="text-sm">Position yourself in the camera frame and follow the exercise routine</p>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}