import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Play, RotateCcw, CheckCircle2, Camera, AlertCircle, Dumbbell, Activity, Zap, Target, Info, Eye } from 'lucide-react';
import { Card, Button } from '../components';
import djangoAPI from '../services/djangoApi';
import { Pose } from '@mediapipe/pose';
import * as cam from '@mediapipe/camera_utils';
import * as draw from '@mediapipe/drawing_utils';

import { API_URL as BASE_URL } from '../config/api';

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
    const [showReference, setShowReference] = useState(false);
    const videoRef = useRef(null);
    const canvasRef = useRef(null);

    // Redirect if no exercise data
    useEffect(() => {
        if (!exercise) {
            navigate('/patient/exercises');
        }
    }, [exercise, navigate]);

    const handleStartWorkout = async () => {
        try {
            setError(null);
            setCameraPermission('granted');

            // Try to start backend session
            try {
                if (exercise.id === 'bicep-curl') {
                    await djangoAPI.exercise.startBicepWorkout(exercise.targetReps);
                } else {
                    await djangoAPI.exercise.startWorkout(exercise.targetReps);
                }
            } catch (e) {
                console.warn("Backend session start failed, but continuing with local AI:", e);
            }

            setWorkoutStarted(true);
            pollWorkoutStatus();
        } catch (err) {
            console.error('Failed to start workout:', err);
            setError('Failed to start workout. Please ensure camera access.');
        }
    };


    // AI State
    const [reps, setReps] = useState(0);
    const [feedback, setFeedback] = useState("Position yourself in frame");
    const [stage, setStage] = useState("down");
    const [hudData, setHudData] = useState({
        leftAngle: 0,
        rightAngle: 0,
        excellent: 0,
        good: 0,
        partial: 0,
        diff: 0
    });

    const repsRef = useRef(0);
    const stageRef = useRef("down");
    const qualityRef = useRef({ excellent: 0, good: 0, partial: 0 });
    const poseRef = useRef(null);

    const calculateAngle = (a, b, c) => {
        if (!a || !b || !c) return 0;
        const radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
        let angle = Math.abs((radians * 180.0) / Math.PI);
        if (angle > 180.0) angle = 360 - angle;
        return Math.round(angle);
    };

    useEffect(() => {
        if (!workoutStarted || !videoRef.current || !canvasRef.current) return;

        const video = videoRef.current;
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d', { alpha: false });

        const pose = new Pose({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose@0.5.1675469404/${file}`,
        });

        pose.setOptions({
            modelComplexity: 2, // High accuracy model
            smoothLandmarks: true,
            minDetectionConfidence: 0.6,
            minTrackingConfidence: 0.6,
        });

        pose.onResults((results) => {
            if (!ctx) return;
            if (canvas.width !== results.image.width) {
                canvas.width = results.image.width;
                canvas.height = results.image.height;
            }

            // Draw Mirror Image
            ctx.save();
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.scale(-1, 1);
            ctx.drawImage(results.image, -canvas.width, 0, canvas.width, canvas.height);
            ctx.restore();

            if (results.poseLandmarks) {
                const landmarks = results.poseLandmarks;

                // Mirror mapping function for landmarks to match the mirrored video feed
                const getX = (p) => (1 - p.x) * canvas.width;
                const getY = (p) => p.y * canvas.height;

                // Define Major Joint Connections
                const MAJOR_CONNECTIONS = [
                    [11, 12], // shoulders
                    [11, 13], [13, 15], // left arm
                    [12, 14], [14, 16], // right arm
                    [11, 23], [12, 24], // torso
                    [23, 24], // hips
                    [23, 25], [25, 27], // left leg
                    [24, 26], [26, 28]  // right leg
                ];

                // Draw Connections
                MAJOR_CONNECTIONS.forEach(([i, j]) => {
                    const start = landmarks[i];
                    const end = landmarks[j];
                    if (start && end && (start.visibility > 0.5 && end.visibility > 0.5)) {
                        ctx.beginPath();
                        ctx.moveTo(getX(start), getY(start));
                        ctx.lineTo(getX(end), getY(end));
                        ctx.lineWidth = 6;
                        ctx.strokeStyle = '#3B82F6';
                        ctx.lineCap = 'round';
                        ctx.stroke();
                    }
                });

                // Draw Major Joint Dots
                [11, 12, 13, 14, 15, 16, 23, 24, 25, 26].forEach(index => {
                    const p = landmarks[index];
                    if (p && p.visibility > 0.5) {
                        ctx.beginPath();
                        ctx.arc(getX(p), getY(p), 6, 0, 2 * Math.PI);
                        ctx.fillStyle = '#FFFFFF';
                        ctx.fill();
                        ctx.lineWidth = 2;
                        ctx.strokeStyle = '#3B82F6';
                        ctx.stroke();
                    }
                });

                const syncRepWithBackend = async (currentAngle, quality) => {
                    try {
                        const isCompleted = repsRef.current >= exercise.targetReps;
                        await djangoAPI.exercise.updateSessionData({
                            exercise_id: exercise.id,
                            reps: repsRef.current,
                            angle: currentAngle,
                            stage: stageRef.current,
                            completed: isCompleted,
                            quality: quality
                        });
                    } catch (err) { }
                };

                const drawAngleText = (point, angle) => {
                    ctx.save();
                    ctx.fillStyle = "#FACC15";
                    ctx.font = "bold 24px Inter";
                    ctx.shadowBlur = 4;
                    ctx.shadowColor = "rgba(0,0,0,0.5)";
                    ctx.fillText(`${angle}°`, getX(point) - 40, getY(point) - 10);
                    ctx.restore();
                };

                // BILATERAL LOGIC HANDLER
                if (exercise.id === 'bicep-curl') {
                    const lAngle = calculateAngle(landmarks[11], landmarks[13], landmarks[15]);
                    const rAngle = calculateAngle(landmarks[12], landmarks[14], landmarks[16]);
                    drawAngleText(landmarks[13], lAngle);
                    drawAngleText(landmarks[14], rAngle);
                    const avgAngle = (lAngle + rAngle) / 2;
                    setHudData(prev => ({ ...prev, leftAngle: lAngle, rightAngle: rAngle, diff: Math.abs(lAngle - rAngle) }));

                    if (avgAngle > 160) {
                        if (stageRef.current === "up") {
                            setFeedback("Great! Fully extend and curl again.");
                            syncRepWithBackend(avgAngle, "transition");
                        }
                        stageRef.current = "down";
                        setStage("down");
                    }
                    if (avgAngle < 45 && stageRef.current === "down") {
                        stageRef.current = "up";
                        setStage("up");
                        repsRef.current += 1;
                        setReps(repsRef.current);

                        let quality = avgAngle < 40 ? "excellent" : (avgAngle < 55 ? "good" : "partial");
                        qualityRef.current[quality] += 1;
                        setFeedback(quality === "excellent" ? "Perfect Form!" : "Good, pull higher!");
                        setHudData(prev => ({ ...prev, ...qualityRef.current }));
                        syncRepWithBackend(avgAngle, quality);
                    }
                }
                else if (exercise.id === 'shoulder-extension' || exercise.id === 'arm-raises') {
                    // Lateral or Frontal Raises
                    const lAngle = calculateAngle(landmarks[23], landmarks[11], landmarks[13]);
                    const rAngle = calculateAngle(landmarks[24], landmarks[12], landmarks[14]);
                    drawAngleText(landmarks[11], lAngle);
                    drawAngleText(landmarks[12], rAngle);

                    const avgAngle = (lAngle + rAngle) / 2;
                    setHudData(prev => ({ ...prev, leftAngle: lAngle, rightAngle: rAngle, diff: Math.abs(lAngle - rAngle) }));

                    // Shrug check
                    const nose = landmarks[0];
                    if ((landmarks[11].y + landmarks[12].y) / 2 < (nose.y + 0.05)) {
                        setFeedback("DON'T SHRUG!");
                    }

                    if (avgAngle < 30) {
                        stageRef.current = "down";
                        setStage("down");
                    }
                    if (avgAngle > 85 && stageRef.current === "down") {
                        stageRef.current = "up";
                        setStage("up");
                        repsRef.current += 1;
                        setReps(repsRef.current);

                        let quality = avgAngle > 90 ? "excellent" : (avgAngle > 75 ? "good" : "partial");
                        qualityRef.current[quality] += 1;
                        setFeedback("Good lift! Controlled descent now.");
                        setHudData(prev => ({ ...prev, ...qualityRef.current }));
                        syncRepWithBackend(avgAngle, quality);
                    }
                }
                else if (exercise.id === 'jumping-jacks') {
                    // Jumping Jacks logic
                    const lAngleLegs = calculateAngle(landmarks[11], landmarks[23], landmarks[25]);
                    const rAngleLegs = calculateAngle(landmarks[12], landmarks[24], landmarks[26]);
                    const lAngleArms = calculateAngle(landmarks[23], landmarks[11], landmarks[13]);
                    const rAngleArms = calculateAngle(landmarks[24], landmarks[12], landmarks[14]);

                    const legAvg = (lAngleLegs + rAngleLegs) / 2;
                    const armAvg = (lAngleArms + rAngleArms) / 2;

                    setHudData(prev => ({ ...prev, leftAngle: armAvg, rightAngle: legAvg, diff: Math.abs(armAvg - legAvg) }));

                    if (armAvg < 40 && legAvg < 170) {
                        stageRef.current = "down";
                        setStage("down");
                    }
                    if (armAvg > 150 && legAvg > 175 && stageRef.current === "down") {
                        stageRef.current = "up";
                        setStage("up");
                        repsRef.current += 1;
                        setReps(repsRef.current);
                        qualityRef.current.excellent += 1;
                        setFeedback("Keep moving! Dynamic tempo!");
                        setHudData(prev => ({ ...prev, excellent: qualityRef.current.excellent }));
                        syncRepWithBackend(180, "excellent");
                    }
                }
            }
        });

        const camera = new cam.Camera(video, {
            onFrame: async () => { await pose.send({ image: video }); },
            width: 1280,
            height: 720,
        });

        camera.start();
        return () => { camera.stop(); pose.close(); };
    }, [workoutStarted, exercise.id]);

    const pollWorkoutStatus = async () => {
        try {
            const status = exercise.id === 'bicep-curl' ? await djangoAPI.exercise.getBicepStatus() : await djangoAPI.exercise.getWorkoutStatus();
            setWorkoutStatus(status);
            if (workoutStarted && !status.completed) setTimeout(pollWorkoutStatus, 1000);
        } catch (err) { }
    };

    const handleResetWorkout = async () => {
        try {
            if (videoRef.current && videoRef.current.srcObject) {
                const tracks = videoRef.current.srcObject.getTracks();
                tracks.forEach(track => track.stop());
                videoRef.current.srcObject = null;
            }
            repsRef.current = 0;
            setReps(0);
            setWorkoutStarted(false);
        } catch (err) { }
    };

    if (!exercise) return null;
    const Icon = exerciseIcons[exercise.id] || Activity;

    return (
        <div className="min-h-screen bg-slate-50">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <button onClick={() => navigate('/patient/exercises')} className="p-2 hover:bg-slate-100 rounded-full transition-colors text-slate-500">
                            <ArrowLeft className="w-6 h-6" />
                        </button>
                        <div>
                            <h1 className="text-xl font-black text-slate-900 leading-none mb-1">{exercise.name}</h1>
                            <div className="flex items-center gap-2 text-xs font-bold text-slate-500 uppercase tracking-widest">
                                <span className={`px-2 py-0.5 rounded bg-${exercise.color}-100 text-${exercise.color}-700`}>{exercise.id}</span>
                                <span>•</span>
                                <span>{exercise.targetReps} Reps Target</span>
                            </div>
                        </div>
                    </div>
                    <Button variant="secondary" size="sm" icon={Eye} onClick={() => setShowReference(!showReference)}>
                        {showReference ? "Close Reference" : "Show Reference"}
                    </Button>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-6 py-8">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Main Tracker */}
                    <div className="lg:col-span-2 space-y-6">
                        <div className="relative bg-black rounded-3xl overflow-hidden shadow-2xl group border-4 border-white aspect-video">
                            <video ref={videoRef} className="absolute opacity-0 pointer-events-none" playsInline muted />
                            <canvas ref={canvasRef} className="w-full h-full object-cover" />

                            {!workoutStarted && (
                                <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-md flex items-center justify-center p-12 text-center z-20">
                                    <div className="max-w-md animate-in fade-in zoom-in duration-500">
                                        <div className="w-24 h-24 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-8 ring-8 ring-emerald-500/10">
                                            <Activity className="w-12 h-12 text-emerald-400" />
                                        </div>
                                        <h2 className="text-3xl font-black text-white mb-4 uppercase tracking-tighter">Initialize AI Tracker</h2>
                                        <p className="text-white/70 mb-8 text-lg font-medium">Position your full body in the frame. The AI will curate your form and count reps automatically.</p>
                                        <button onClick={handleStartWorkout} className="w-full bg-emerald-500 hover:bg-emerald-400 text-white font-black py-4 rounded-2xl shadow-xl shadow-emerald-500/20 transform hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3 text-lg">
                                            <Play className="w-6 h-6 fill-current" /> START WORKOUT
                                        </button>
                                    </div>
                                </div>
                            )}

                            {workoutStarted && (
                                <>
                                    {/* AI HUD (Top-Left) */}
                                    <div className="absolute top-6 left-6 bg-slate-900/90 backdrop-blur-xl p-5 rounded-3xl border border-white/10 z-10 w-52 shadow-2xl">
                                        <div className="space-y-4">
                                            <div className="flex justify-between items-end border-b border-white/5 pb-3">
                                                <div>
                                                    <p className="text-white/40 text-[10px] font-black uppercase tracking-widest mb-1">Reps</p>
                                                    <p className="text-white text-3xl font-black leading-none">{reps}<span className="text-white/20 text-sm font-normal ml-1">/{exercise.targetReps}</span></p>
                                                </div>
                                                <div className="text-right">
                                                    <p className="text-white/40 text-[10px] font-black uppercase tracking-widest mb-1">Stage</p>
                                                    <p className={`text-xs font-black uppercase tracking-widest px-2 py-0.5 rounded ${stage === 'up' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-blue-500/20 text-blue-400'}`}>{stage}</p>
                                                </div>
                                            </div>

                                            <div className="grid grid-cols-3 gap-2 text-center">
                                                <div className="bg-emerald-500/10 p-2 rounded-xl border border-emerald-500/20">
                                                    <p className="text-[9px] font-black text-emerald-400 mb-0.5">EXC</p>
                                                    <p className="text-white text-sm font-black">{hudData.excellent}</p>
                                                </div>
                                                <div className="bg-yellow-500/10 p-2 rounded-xl border border-yellow-500/20">
                                                    <p className="text-[9px] font-black text-yellow-400 mb-0.5">GOOD</p>
                                                    <p className="text-white text-sm font-black">{hudData.good}</p>
                                                </div>
                                                <div className="bg-orange-500/10 p-2 rounded-xl border border-orange-500/20">
                                                    <p className="text-[9px] font-black text-orange-400 mb-0.5">PRT</p>
                                                    <p className="text-white text-sm font-black">{hudData.partial}</p>
                                                </div>
                                            </div>

                                            <div className="space-y-2 pt-1">
                                                <div className="flex justify-between items-center text-[10px] font-bold text-white/50 uppercase">
                                                    <span>Symmetry</span>
                                                    <span className={`${hudData.diff > 15 ? 'text-red-400' : 'text-emerald-400'}`}>{hudData.diff}° Diff</span>
                                                </div>
                                                <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                                                    <div className={`h-full transition-all duration-300 ${hudData.diff > 15 ? 'bg-red-400' : 'bg-emerald-400'}`}
                                                        style={{ width: `${Math.max(5, 100 - (hudData.diff * 2))}%` }}></div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Live Banner */}
                                    <div className="absolute top-6 right-6 z-10 flex items-center gap-3 bg-black/40 backdrop-blur-md px-4 py-2 rounded-2xl border border-white/10 uppercase tracking-tighter text-[11px] font-black text-white">
                                        <div className="w-2 h-2 bg-rose-500 rounded-full animate-pulse shadow-[0_0_10px_#f43f5e]"></div>
                                        Live AI Telemetry
                                    </div>

                                    {/* AI Coaching Panel */}
                                    <div className="absolute bottom-8 left-1/2 -translate-x-1/2 w-full max-w-md px-6 z-30">
                                        <div className={`p-5 rounded-3xl border shadow-2xl flex items-center gap-5 transition-all duration-300 ${feedback.includes("DON'T") ? "bg-rose-500 border-rose-400 text-white animate-bounce" : "bg-slate-900/95 backdrop-blur-xl border-white/10 text-white"
                                            }`}>
                                            <div className={`w-14 h-14 rounded-2xl flex items-center justify-center shrink-0 ${feedback.includes("DON'T") ? "bg-white/20" : "bg-emerald-500/20"}`}>
                                                <Zap className={`w-8 h-8 ${feedback.includes("DON'T") ? "text-white" : "text-emerald-400"}`} />
                                            </div>
                                            <div>
                                                <p className="text-[10px] font-black uppercase tracking-[0.2em] mb-1 opacity-60">AI Coach Guidance</p>
                                                <p className="text-xl font-black leading-tight tracking-tight uppercase">{feedback}</p>
                                            </div>
                                        </div>
                                    </div>
                                </>
                            )}

                            {/* Reference Video Overlay */}
                            {showReference && exercise.videoUrl && (
                                <div className="absolute top-6 right-6 w-64 aspect-video rounded-2xl overflow-hidden border-2 border-white/20 shadow-2xl z-40 bg-black animate-in slide-in-from-right duration-300 cursor-move">
                                    <div className="absolute top-0 left-0 right-0 bg-black/60 p-2 flex justify-between items-center z-10">
                                        <span className="text-[9px] font-black text-white/80 uppercase">Doctor's Demo</span>
                                        <button onClick={() => setShowReference(false)} className="text-white/60 hover:text-white">✕</button>
                                    </div>
                                    <video src={`${BASE_URL}${exercise.videoUrl}`} autoPlay loop muted className="w-full h-full object-cover" />
                                </div>
                            )}
                        </div>

                        {/* Exercise Context */}
                        <Card className="bg-white border-slate-200">
                            <div className="flex items-start gap-4">
                                <div className="p-3 bg-blue-50 rounded-2xl">
                                    <Info className="w-6 h-6 text-blue-500" />
                                </div>
                                <div>
                                    <h3 className="font-black text-slate-900 uppercase tracking-tighter mb-2">Instructions & Medical Targets</h3>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                                            <p className="text-[10px] font-black text-slate-400 uppercase mb-1">Target Angle</p>
                                            <p className="text-sm font-bold text-slate-700">{exercise.id === 'bicep-curl' ? '< 45°' : '> 85°'}</p>
                                        </div>
                                        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                                            <p className="text-[10px] font-black text-slate-400 uppercase mb-1">Pace</p>
                                            <p className="text-sm font-bold text-slate-700">Moderate (2s/rep)</p>
                                        </div>
                                        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                                            <p className="text-[10px] font-black text-slate-400 uppercase mb-1">Focus</p>
                                            <p className="text-sm font-bold text-slate-700">Full extension</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </Card>
                    </div>

                    {/* Sidebar Controls */}
                    <div className="space-y-6">
                        <Card className="p-8 text-center bg-white border-slate-200">
                            <p className="text-xs font-black text-slate-400 uppercase tracking-widest mb-4">Total Completion</p>
                            <div className="relative w-32 h-32 mx-auto mb-6">
                                <svg className="w-full h-full transform -rotate-90">
                                    <circle cx="64" cy="64" r="58" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-slate-100" />
                                    <circle cx="64" cy="64" r="58" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-emerald-500 transition-all duration-1000"
                                        strokeDasharray={364} strokeDashoffset={364 - (364 * Math.min(100, (reps / exercise.targetReps) * 100)) / 100} />
                                </svg>
                                <div className="absolute inset-0 flex flex-col items-center justify-center">
                                    <p className="text-3xl font-black text-slate-900 leading-none">{reps}</p>
                                    <p className="text-[10px] font-black text-slate-400 uppercase">of {exercise.targetReps}</p>
                                </div>
                            </div>
                            {reps >= exercise.targetReps ? (
                                <div className="p-4 bg-emerald-50 text-emerald-700 rounded-2xl border border-emerald-100 font-black animate-pulse">
                                    TARGET ACHIEVED!
                                </div>
                            ) : (
                                <Button variant="secondary" className="w-full py-4 rounded-xl" icon={RotateCcw} onClick={handleResetWorkout}>
                                    RESET SESSION
                                </Button>
                            )}
                        </Card>

                        <Card className="bg-indigo-600 text-white border-none overflow-hidden relative">
                            <div className="relative z-10">
                                <h3 className="font-black text-lg uppercase tracking-tight mb-2">Precision AI Analysis</h3>
                                <p className="text-white/80 text-sm leading-relaxed mb-6">Every movement is being analyzed for joint alignment and velocity. Results are synced with your recovery timeline.</p>
                                <Button className="w-full bg-white/20 hover:bg-white/30 text-white border-none py-4" icon={Info}>
                                    View Metric Breakdown
                                </Button>
                            </div>
                            <div className="absolute -bottom-12 -right-12 w-48 h-48 bg-white/10 rounded-full blur-3xl"></div>
                        </Card>
                    </div>
                </div>
            </div>
        </div>
    );
}
