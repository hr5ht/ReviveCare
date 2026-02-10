import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Dumbbell, ArrowLeft, Activity, Zap, Target } from 'lucide-react';
import { Card } from '../components';

const exercises = [
    {
        id: 'bicep-curl',
        name: 'Bicep Curl',
        description: 'Strengthen your biceps with controlled arm movements',
        icon: Dumbbell,
        color: 'emerald',
        endpoint: '/bc',
        targetReps: 12,
        hasCamera: true,
        videoUrl: '/static/Patients/videos/bc.mp4'
    },
    {
        id: 'shoulder-extension',
        name: 'Lateral Raise',
        description: 'Improve shoulder mobility and strength',
        icon: Activity,
        color: 'blue',
        endpoint: '/sr',
        targetReps: 10,
        hasCamera: true,
        videoUrl: '/static/Patients/videos/sl.mp4'
    },
    {
        id: 'jumping-jacks',
        name: 'Jumping Jacks',
        description: 'Full-body cardio warmup exercise',
        icon: Zap,
        color: 'purple',
        endpoint: '/jj',
        targetReps: 20,
        hasCamera: true,
        videoUrl: '/static/Patients/videos/jj.mp4'
    },
    {
        id: 'arm-raises',
        name: 'Arm Raises',
        description: 'Build shoulder endurance and stability',
        icon: Target,
        color: 'orange',
        endpoint: '/ar',
        targetReps: 15,
        hasCamera: true,
        videoUrl: '/static/Patients/videos/ar.mp4'
    }
];

export default function ExerciseSelection() {
    const navigate = useNavigate();

    const handleExerciseClick = (exercise) => {
        // Pass only serializable data (no icon component)
        const exerciseData = {
            id: exercise.id,
            name: exercise.name,
            description: exercise.description,
            color: exercise.color,
            endpoint: exercise.endpoint,
            targetReps: exercise.targetReps,
            hasCamera: exercise.hasCamera,
            videoUrl: exercise.videoUrl
        };

        navigate(`/patient/exercise/${exercise.id}`, {
            state: { exercise: exerciseData }
        });
    };

    const getColorClasses = (color) => {
        const colors = {
            emerald: 'from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700',
            blue: 'from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700',
            purple: 'from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700',
            orange: 'from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700'
        };
        return colors[color] || colors.emerald;
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-emerald-50/20">
            {/* Header */}
            <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200 shadow-sm">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <button
                        onClick={() => navigate('/patient/dashboard')}
                        className="flex items-center gap-2 text-slate-600 hover:text-slate-900 transition-colors mb-2"
                    >
                        <ArrowLeft className="w-5 h-5" />
                        <span className="font-medium">Back to Dashboard</span>
                    </button>
                    <h1 className="text-2xl font-bold text-gray-900">Exercise Programs</h1>
                    <p className="text-gray-600">Choose an exercise to begin your workout</p>
                </div>
            </div>

            {/* Exercise Cards */}
            <div className="max-w-7xl mx-auto px-6 py-12">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
                    {exercises.map((exercise) => {
                        const Icon = exercise.icon;
                        return (
                            <Card
                                key={exercise.id}
                                className="group cursor-pointer transition-all duration-300 hover:scale-105 hover:shadow-xl"
                                onClick={() => handleExerciseClick(exercise)}
                            >
                                <div className="flex items-start gap-4">
                                    {/* Icon */}
                                    <div className={`w-16 h-16 bg-gradient-to-br ${getColorClasses(exercise.color)} rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg group-hover:scale-110 transition-transform`}>
                                        <Icon className="w-8 h-8 text-white" />
                                    </div>

                                    {/* Content */}
                                    <div className="flex-1">
                                        <div className="flex items-start justify-between mb-2">
                                            <h3 className="text-xl font-bold text-gray-900 group-hover:text-emerald-600 transition-colors">
                                                {exercise.name}
                                            </h3>
                                            {exercise.hasCamera && (
                                                <span className="px-2 py-1 bg-emerald-100 text-emerald-700 text-xs font-semibold rounded-full">
                                                    AI Tracking
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-gray-600 mb-3">{exercise.description}</p>
                                        <div className="flex items-center gap-4 text-sm text-gray-500">
                                            <div className="flex items-center gap-1">
                                                <Target className="w-4 h-4" />
                                                <span>{exercise.targetReps} reps</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Action hint */}
                                <div className="mt-4 pt-4 border-t border-gray-200">
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-gray-500">Click to start</span>
                                        <ArrowLeft className="w-4 h-4 text-gray-400 rotate-180 group-hover:translate-x-1 transition-transform" />
                                    </div>
                                </div>
                            </Card>
                        );
                    })}
                </div>

                {/* Info Box */}
                <Card className="mt-8 bg-blue-50 border-blue-200">
                    <div className="flex items-start gap-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                            <Activity className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-gray-900 mb-1">AI-Powered Exercise Tracking</h3>
                            <p className="text-sm text-gray-700 leading-relaxed">
                                Exercises marked with "AI Tracking" use your camera to analyze your form in real-time
                                and count your reps automatically. Make sure to grant camera permissions when prompted.
                            </p>
                        </div>
                    </div>
                </Card>
            </div>
        </div>
    );
}
