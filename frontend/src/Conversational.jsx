import React, { useState, useRef, useEffect } from "react";
import "./index.css"; // import fonts + utilities

export default function Conversational() {
    const [status, setStatus] = useState("idle");
    const [transcript, setTranscript] = useState("");
    const [assistantText, setAssistantText] = useState("");
    const [history, setHistory] = useState([]);
    const [error, setError] = useState(null);
    const [showTranscript, setShowTranscript] = useState(false);

    const audioElRef = useRef(null);

    // Recording & VAD state refs
    const mediaStreamRef = useRef(null);
    const mediaRecorderRef = useRef(null);
    const recordedChunksRef = useRef([]);
    const audioCtxRef = useRef(null);
    const analyserRef = useRef(null);
    const sourceRef = useRef(null);
    const vadIntervalRef = useRef(null);
    const silenceStartRef = useRef(null);
    const timeoutStopRef = useRef(null);

    // Config
    const VAD_CHECK_INTERVAL_MS = 100;
    const SILENCE_THRESHOLD = 0.01;
    const SILENCE_DETECT_MS = 1800;
    const RECORDING_TAIL_MS = 300;
    const MAX_RECORDING_MS = 100_000;

    // Play base64 audio
    function playBase64Audio(base64, mime = "audio/mpeg") {
        return new Promise((resolve, reject) => {
            try {
                const byteString = atob(base64);
                const ab = new ArrayBuffer(byteString.length);
                const ia = new Uint8Array(ab);
                for (let i = 0; i < byteString.length; i++) ia[i] = byteString.charCodeAt(i);
                const blob = new Blob([ab], { type: mime });
                const url = URL.createObjectURL(blob);
                const audio = audioElRef.current;
                if (!audio) {
                    reject(new Error("No audio element available"));
                    return;
                }
                audio.src = url;
                audio.onended = () => {
                    resolve();
                };
                audio.onerror = (e) => {
                    reject(e);
                };
                audio.play().catch((e) => {
                    console.warn("Playback may be blocked:", e);
                    resolve();
                });
            } catch (e) {
                reject(e);
            }
        });
    }

    // Start flow
    async function handleStartCallTypes() {
        setError(null);
        setAssistantText("");
        setTranscript("");
        setStatus("playing_prompt");
        try {
            const res = await fetch("http://localhost:5000/api/converse/start_language");
            const data = await res.json();
            if (data.audio_base64) {
                await playBase64Audio(data.audio_base64, data.mime || "audio/mpeg");
            }
            setStatus("ready_record");
        } catch (e) {
            console.error(e);
            setError("Connection failed. Please try again.");
            setStatus("idle");
        }
    }

    // Cleanup audio resources
    function cleanupRecordingResources() {
        if (vadIntervalRef.current) {
            clearInterval(vadIntervalRef.current);
            vadIntervalRef.current = null;
        }
        if (timeoutStopRef.current) {
            clearTimeout(timeoutStopRef.current);
            timeoutStopRef.current = null;
        }
        if (audioCtxRef.current) {
            try {
                audioCtxRef.current.close();
            } catch (e) { }
            audioCtxRef.current = null;
        }
        try {
            if (sourceRef.current) {
                sourceRef.current.disconnect();
                sourceRef.current = null;
            }
            if (analyserRef.current) {
                analyserRef.current.disconnect();
                analyserRef.current = null;
            }
        } catch (e) { }
        if (mediaStreamRef.current) {
            try {
                mediaStreamRef.current.getTracks().forEach((t) => t.stop());
            } catch (e) { }
            mediaStreamRef.current = null;
        }
    }

    // Start recording with VAD
    async function startRecording() {
        setError(null);

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            setError("Microphone not supported in this browser.");
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaStreamRef.current = stream;

            const options = { mimeType: "audio/webm" };
            const mr = new MediaRecorder(stream, options);
            mediaRecorderRef.current = mr;
            recordedChunksRef.current = [];

            mr.ondataavailable = (ev) => {
                if (ev.data && ev.data.size > 0) recordedChunksRef.current.push(ev.data);
            };

            mr.onerror = (e) => {
                console.error("MediaRecorder error", e);
                setError("Recording error: " + e?.message);
                stopRecordingImmediate();
            };

            mr.onstart = () => {
                setStatus("recording");
                timeoutStopRef.current = setTimeout(() => {
                    stopRecording();
                }, MAX_RECORDING_MS);
            };

            mr.start(250);

            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            audioCtxRef.current = audioCtx;
            const source = audioCtx.createMediaStreamSource(stream);
            sourceRef.current = source;
            const analyser = audioCtx.createAnalyser();
            analyser.fftSize = 2048;
            analyserRef.current = analyser;

            source.connect(analyser);

            const dataArray = new Float32Array(analyser.fftSize);
            silenceStartRef.current = null;

            vadIntervalRef.current = setInterval(() => {
                try {
                    analyser.getFloatTimeDomainData(dataArray);
                    let sumSquares = 0;
                    for (let i = 0; i < dataArray.length; i++) {
                        const v = dataArray[i];
                        sumSquares += v * v;
                    }
                    const rms = Math.sqrt(sumSquares / dataArray.length);

                    if (rms < SILENCE_THRESHOLD) {
                        if (silenceStartRef.current == null) {
                            silenceStartRef.current = Date.now();
                        } else {
                            const elapsed = Date.now() - silenceStartRef.current;
                            if (elapsed >= SILENCE_DETECT_MS) {
                                setTimeout(() => {
                                    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
                                        stopRecording();
                                    }
                                }, RECORDING_TAIL_MS);
                                clearInterval(vadIntervalRef.current);
                                vadIntervalRef.current = null;
                            }
                        }
                    } else {
                        silenceStartRef.current = null;
                    }
                } catch (e) {
                    console.warn("VAD error", e);
                }
            }, VAD_CHECK_INTERVAL_MS);
        } catch (e) {
            console.error(e);
            setError("Microphone access denied");
            stopRecordingImmediate();
        }
    }

    // Stop recording
    function stopRecording() {
        if (vadIntervalRef.current) {
            clearInterval(vadIntervalRef.current);
            vadIntervalRef.current = null;
        }
        if (timeoutStopRef.current) {
            clearTimeout(timeoutStopRef.current);
            timeoutStopRef.current = null;
        }
        const mr = mediaRecorderRef.current;
        if (mr && (mr.state === "recording" || mr.state === "paused")) {
            try {
                mr.stop();
            } catch (e) {
                console.warn("stop error", e);
            }
        } else {
            stopRecordingImmediate();
        }

        setTimeout(() => {
            finalizeRecordingAndUpload();
        }, 400);
    }

    // Force stop
    function stopRecordingImmediate() {
        try {
            if (mediaRecorderRef.current && (mediaRecorderRef.current.state === "recording" || mediaRecorderRef.current.state === "paused")) {
                try { mediaRecorderRef.current.stop(); } catch (e) { }
            }
        } catch (e) { }
        cleanupRecordingResources();
        mediaRecorderRef.current = null;
        recordedChunksRef.current = [];
        setStatus("ready_record");
    }

    // Finalize recording and upload
    async function finalizeRecordingAndUpload() {
        try {
            setStatus("uploading");
            const pieces = recordedChunksRef.current || [];
            if (!pieces || pieces.length === 0) {
                setStatus("ready_record");
                return;
            }
            const blob = new Blob(pieces, { type: "audio/webm" });
            cleanupRecordingResources();
            mediaRecorderRef.current = null;
            recordedChunksRef.current = [];
            await uploadAudioBlob(blob);
        } catch (e) {
            console.error(e);
            setError("Upload failed. Please try again.");
            cleanupRecordingResources();
            setStatus("ready_record");
        }
    }

    // Upload audio blob
    async function uploadAudioBlob(blob) {
        setError(null);
        setStatus("uploading");
        const fd = new FormData();
        fd.append("audio", blob, "reply.webm");
        fd.append("history", JSON.stringify(history || []));

        try {
            const res = await fetch("http://localhost:5000/api/converse/submit_audio", {
                method: "POST",
                body: fd
            });
            const data = await res.json();
            if (data.transcript) {
                setTranscript(data.transcript);
                setHistory((h) => [...h, { role: "user", text: data.transcript }]);
            }
            if (data.assistant_text) {
                setAssistantText(data.assistant_text);
                setHistory((h) => [...h, { role: "assistant", text: data.assistant_text }]);
            }
            if (data.audio_base64) {
                await playBase64Audio(data.audio_base64, data.mime || "audio/mpeg");
            }
        } catch (e) {
            console.error(e);
            setError("Processing failed. Please try again.");
        } finally {
            setStatus("ready_record");
        }
    }

    // Toggle recording
    function handleMicToggle() {
        if (status === "ready_record" || status === "idle") {
            startRecording();
        } else if (status === "recording") {
            stopRecording();
        } else if (status === "idle") {
            handleStartCallTypes();
        }
    }

    // Toggle transcript visibility
    function toggleTranscript() {
        setShowTranscript(!showTranscript);
    }

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            cleanupRecordingResources();
        };
    }, []);

    return (
        <div className="min-h-screen bg-gradient-to-br from-purple-100 via-blue-50 to-pink-100 overflow-hidden relative">
            {/* Floating background blobs */}
            <div className="absolute top-10 left-10 w-72 h-72 bg-gradient-to-br from-purple-300 to-pink-300 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse"></div>
            <div className="absolute top-20 right-10 w-64 h-64 bg-gradient-to-br from-blue-300 to-purple-300 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse delay-1000"></div>
            <div className="absolute bottom-10 left-1/2 w-80 h-80 bg-gradient-to-br from-pink-300 to-blue-300 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse delay-2000"></div>

            {/* Main container - perfectly centered */}
            <div className="flex flex-col items-center justify-center min-h-screen p-8">
                <div className="text-center space-y-8 relative z-10 w-full max-w-lg">
                    
                    {/* AI Assistant Header */}
                    <div className="mb-8">
                        <h1 className="headline gradient-text text-glow text-3xl md:text-4xl leading-tight tracking-tight text-gray-800 mb-3">
                            I'm Chloe - Your Onboarding Guide
                        </h1>
                        <p className="body-copy ui-text text-gray-600 text-lg leading-relaxed tracking-wide">
                            Talk to me naturally. I'll understand and respond intelligently.
                        </p>
                    </div>
                    
                    {/* Central microphone button - perfectly centered */}
                    <div className="flex justify-center items-center">
                        <div className="relative">
                            <div className={`w-48 h-48 rounded-full flex items-center justify-center shadow-2xl transition-all duration-500 cursor-pointer ${
                                status === "recording" 
                                    ? "bg-gradient-to-br from-red-400 to-pink-500 animate-pulse scale-110" 
                                    : status === "uploading"
                                    ? "bg-gradient-to-br from-blue-400 to-purple-500"
                                    : "bg-gradient-to-br from-purple-500 to-blue-500 hover:scale-105"
                            }`}
                            onClick={status !== "idle" ? handleMicToggle : handleStartCallTypes}>
                                
                                {status === "uploading" ? (
                                    <div className="w-12 h-12 border-4 border-white border-t-transparent rounded-full animate-spin"></div>
                                ) : (
                                    <div className="flex items-center justify-center">
                                        <svg className="w-16 h-16 text-white" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z"/>
                                        </svg>
                                    </div>
                                )}
                            </div>
                            
                            {/* Pulsing rings for recording */}
                            {status === "recording" && (
                                <>
                                    <div className="absolute inset-0 rounded-full border-4 border-red-300 animate-ping"></div>
                                    <div className="absolute inset-0 rounded-full border-2 border-red-200 animate-ping" style={{ animationDelay: '0.5s' }}></div>
                                </>
                            )}
                        </div>
                    </div>

                    {/* Status text */}
                    <div className="text-center">
                        <div className="ui-text text-gray-700 text-xl font-medium">
                            {status === "idle" && "Click to start our conversation"}
                            {status === "playing_prompt" && "Listening..."}
                            {status === "ready_record" && "I'm ready to listen"}
                            {status === "recording" && "I'm listening..."}
                            {status === "uploading" && "Processing your message..."}
                        </div>
                        {status === "idle" && (
                            <p className="body-copy text-gray-500 text-sm mt-2">
                                Tap the microphone and speak naturally
                            </p>
                        )}
                    </div>

                    {/* Error display */}
                    {error && (
                        <div className="bg-red-50 border border-red-200 rounded-2xl p-4 max-w-md mx-auto">
                            <div className="text-red-700 text-center">{error}</div>
                        </div>
                    )}

                    {/* Bottom actions */}
                    <div className="flex items-center justify-center space-x-4 pt-6">
                        <button 
                            onClick={toggleTranscript}
                            className="bg-white/80 backdrop-blur-sm rounded-2xl px-6 py-3 shadow-lg hover:shadow-xl transition-all duration-300 border border-white/30 flex items-center space-x-2 btn-text"
                        >
                            <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                            </svg>
                            <span className="text-gray-700 font-medium">View Conversation</span>
                        </button>
                    </div>

                    {/* Hidden audio element */}
                    <audio ref={audioElRef} className="hidden" />
                </div>
            </div>

            {/* Transcript Overlay */}
            {showTranscript && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 conversation-overlay">
                    <div className="bg-white rounded-3xl max-w-md w-full max-h-[80vh] overflow-y-auto">
                        <div className="p-6">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="text-lg font-bold text-gray-900 headline">Conversation</h3>
                                <button 
                                    onClick={toggleTranscript}
                                    className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center hover:bg-gray-300 transition-colors"
                                >
                                    <span className="text-gray-600 text-lg">×</span>
                                </button>
                            </div>
                            
                            <div className="space-y-3">
                                {history.length === 0 ? (
                                    <div className="text-center text-gray-500 py-8">
                                        <div className="text-4xl mb-2">💬</div>
                                        <div>No conversation yet</div>
                                        <div className="text-sm">Start talking to see transcript</div>
                                    </div>
                                ) : (
                                    history.map((m, i) => (
                                        <div key={i} className={`p-3 rounded-2xl ${
                                            m.role === "user" 
                                                ? "bg-blue-100 text-blue-900 ml-8" 
                                                : "bg-gray-100 text-gray-900 mr-8"
                                        }`}>
                                            <div className="text-xs text-gray-600 mb-1">
                                                {m.role === "user" ? "You" : "Assistant"}
                                            </div>
                                            <div className="text-sm">{m.text}</div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
