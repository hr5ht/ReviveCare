import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Play, Pause, RotateCcw, CheckCircle2, Camera, AlertCircle, Dumbbell, Activity, Zap, Target } from 'lucide-react';
import { Card, Button } from '../components';
import djangoAPI from '../services/djangoApi';

// Map exercise IDs to their icons
const exerciseIcons = {
    'bicep-curl': Dumbbell,
    'shoulder-extension': Activity,
    'jumping-jacks': Zap,
    'arm-raises': Target
};

export default function ExerciseWorkout() {
    const navigate = useNavigate();
    const location = useLocation();
    const exercise = location.state?.exercise;

    const [workoutStarted, setWorkoutStarted] = useState(false);
    const [workoutStatus, setWorkoutStatus] = useState(null);
    const [error, setError] = useState(null);
    const [cameraPermission, setCameraPermission] = useState(null);
    const videoRef = useRef(null);

    // Redirect if no exercise data
    useEffect(() => {
        if (!exercise) {
            navigate('/patient/exercises');
        }
    }, [exercise, navigate]);

    // Note: We don't need to request camera permission here because
    // Django uses OpenCV to capture from the SERVER's camera (cv2.VideoCapture(0))
    // The video feed is streamed to the browser as an image stream

    const handleStartWorkout = async () => {
        try {
            setError(null);
            console.log('Starting workout...');

            // Start the workout session on Django backend
            let response;
            if (exercise.id === 'bicep-curl') {
                response = await djangoAPI.exercise.startBicepWorkout(exercise.targetReps);
            } else {
                response = await djangoAPI.exercise.startWorkout(exercise.targetReps);
            }
            console.log('Workout started:', response);

            setWorkoutStarted(true);

            // Start polling for workout status
            pollWorkoutStatus();
        } catch (err) {
            console.error('Failed to start workout:', err);
            setError('Failed to start workout. Please make sure Django is running.');
        }
    };

    const pollWorkoutStatus = async () => {
        try {
            let status;
            if (exercise.id === 'bicep-curl') {
                status = await djangoAPI.exercise.getBicepStatus();
            } else {
                status = await djangoAPI.exercise.getWorkoutStatus();
            }
            setWorkoutStatus(status);

            // Continue polling if workout is active
            if (workoutStarted && !status.completed) {
                setTimeout(pollWorkoutStatus, 500); // Poll every 500ms
            }
        } catch (err) {
            console.error('Failed to get workout status:', err);
        }
    };

    const handleResetWorkout = async () => {
        try {
            if (exercise.id === 'bicep-curl') {
                await djangoAPI.exercise.resetBicepWorkout();
            } else {
                await djangoAPI.exercise.resetWorkout();
            }
            setWorkoutStatus(null);
            setWorkoutStarted(false);
        } catch (err) {
            console.error('Failed to reset workout:', err);
        }
    };

    if (!exercise) {
        return null;
    }

    // Get the icon component for this exercise
    const Icon = exerciseIcons[exercise.id] || Activity;

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-emerald-50/20">
            {/* Header */}
            <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200 shadow-sm">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <button
                        onClick={() => navigate('/patient/exercises')}
                        className="flex items-center gap-2 text-slate-600 hover:text-slate-900 transition-colors mb-2"
                    >
                        <ArrowLeft className="w-5 h-5" />
                        <span className="font-medium">Back to Exercises</span>
                    </button>
                    <div className="flex items-center gap-3">
                        <div className={`w-12 h-12 bg-gradient-to-br from-${exercise.color}-500 to-${exercise.color}-600 rounded-xl flex items-center justify-center`}>
                            <Icon className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">{exercise.name}</h1>
                            <p className="text-gray-600">{exercise.description}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="max-w-7xl mx-auto px-6 py-8">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Video Feed */}
                    <Card className="lg:col-span-2">
                        <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                            <Camera className="w-5 h-5" />
                            {exercise.hasCamera ? 'Live Camera Feed with AI Tracking' : 'Exercise Video'}
                        </h2>

                        {error && (
                            <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-2">
                                <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
                                <p className="text-sm text-rose-700">{error}</p>
                            </div>
                        )}

                        {exercise.hasCamera ? (
                            <div className="relative bg-black rounded-lg overflow-hidden" style={{ aspectRatio: '16/9' }}>
                                {workoutStarted ? (
                                    <>
                                        <img
                                            ref={videoRef}
                                            src={exercise.id === 'bicep-curl' ? djangoAPI.exercise.getBicepVideoFeedUrl() : djangoAPI.exercise.getVideoFeedUrl()}
                                            alt="Exercise video feed"
                                            className="w-full h-full object-contain"
                                            onError={(e) => {
                                                console.error('Video feed error:', e);
                                                setError('Failed to load video feed. Make sure your camera is connected and Django is running.');
                                            }}
                                            onLoad={() => {
                                                console.log('Video feed loaded successfully');
                                            }}
                                        />
                                        {/* Loading overlay */}
                                        <div className="absolute top-4 right-4 bg-black/70 px-3 py-1 rounded-full">
                                            <div className="flex items-center gap-2">
                                                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                                                <span className="text-white text-sm">Live</span>
                                            </div>
                                        </div>
                                    </>
                                ) : (
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <div className="text-center text-white">
                                            {cameraPermission === 'denied' ? (
                                                <>
                                                    <Camera className="w-16 h-16 mx-auto mb-4 opacity-50" />
                                                    <p className="text-lg mb-2">Camera Access Required</p>
                                                    <p className="text-sm opacity-75">Please enable camera permissions in your browser settings</p>
                                                </>
                                            ) : (
                                                <>
                                                    <Play className="w-16 h-16 mx-auto mb-4 opacity-50" />
                                                    <p className="text-lg mb-2">Ready to Start</p>
                                                    <p className="text-sm opacity-75">Click "Start Workout" to begin camera tracking</p>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="bg-gray-100 rounded-lg flex items-center justify-center" style={{ aspectRatio: '16/9' }}>
                                <div className="text-center text-gray-500">
                                    <Icon className="w-16 h-16 mx-auto mb-4" />
                                    <p>Exercise demonstration coming soon</p>
                                </div>
                            </div>
                        )}
                    </Card>

                    {/* Stats & Controls */}
                    <div className="space-y-6">
                        {/* Workout Stats */}
                        {workoutStatus && (
                            <Card>
                                <h3 className="font-bold text-gray-900 mb-4">Workout Progress</h3>
                                <div className="space-y-3">
                                    <div>
                                        <div className="flex justify-between text-sm mb-1">
                                            <span className="text-gray-600">Reps Completed</span>
                                            <span className="font-bold text-emerald-600">
                                                {workoutStatus.reps_count || 0} / {exercise.targetReps}
                                            </span>
                                        </div>
                                        <div className="w-full bg-gray-200 rounded-full h-2">
                                            <div
                                                className="bg-emerald-500 h-2 rounded-full transition-all"
                                                style={{ width: `${((workoutStatus.reps_count || 0) / exercise.targetReps) * 100}%` }}
                                            />
                                        </div>
                                    </div>

                                    {workoutStatus.completed && (
                                        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center gap-2">
                                            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                                            <span className="text-sm font-medium text-emerald-700">Workout Complete!</span>
                                        </div>
                                    )}
                                </div>
                            </Card>
                        )}

                        {/* Controls */}
                        <Card>
                            <h3 className="font-bold text-gray-900 mb-4">Controls</h3>
                            <div className="space-y-3">
                                {!workoutStarted ? (
                                    <Button
                                        variant="primary"
                                        size="lg"
                                        className="w-full"
                                        icon={Play}
                                        onClick={handleStartWorkout}
                                        disabled={cameraPermission === 'denied' && exercise.hasCamera}
                                    >
                                        Start Workout
                                    </Button>
                                ) : (
                                    <Button
                                        variant="secondary"
                                        size="lg"
                                        className="w-full"
                                        icon={RotateCcw}
                                        onClick={handleResetWorkout}
                                    >
                                        Reset
                                    </Button>
                                )}
                            </div>
                        </Card>

                        {/* Instructions */}
                        <Card className="bg-blue-50 border-blue-200">
                            <h3 className="font-bold text-gray-900 mb-2">Instructions</h3>
                            <ul className="text-sm text-gray-700 space-y-2">
                                <li>• Position yourself in front of the camera</li>
                                <li>• Ensure good lighting</li>
                                <li>• Follow the on-screen form guidance</li>
                                <li>• Complete {exercise.targetReps} reps at a steady pace</li>
                            </ul>
                        </Card>
                    </div>
                </div>
            </div>
        </div>
    );
}
