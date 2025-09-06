// src/VideoEditor.jsx
import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import { Upload, Mic, MicOff, Send, Video, History, X } from "lucide-react";

export default function VideoEditor() {
    const [messages, setMessages] = useState([]);
    const [conversationState, setConversationState] = useState("upload_video");
    const [history, setHistory] = useState([]);
    const [promptHistory, setPromptHistory] = useState([]);
    const [listening, setListening] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState(null);
    const [inputText, setInputText] = useState("");
    const recognitionRef = useRef(null);
    const audioRef = useRef(null); // for playing ElevenLabs audio
    const hasGreetedRef = useRef(false); // guard to avoid duplicate greeting on mount (StrictMode)

    // Initialize SpeechRecognition once per mount
    useEffect(() => {
        if ("SpeechRecognition" in window || "webkitSpeechRecognition" in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recog = new SpeechRecognition();
            recog.continuous = false;
            recog.interimResults = false;

            recog.onresult = (event) => {
                try {
                    const transcript = event.results[0][0].transcript.trim();
                    setListening(false);
                    handleUserInput(transcript);
                } catch (e) {
                    console.warn("Recognition result parsing error", e);
                }
            };

            recog.onend = () => {
                setListening(false);
            };

            recog.onerror = (e) => {
                setError(`Speech recognition error: ${e?.message || e}`);
                setListening(false);
            };

            recognitionRef.current = recog;
        }

        // cleanup on unmount
        return () => {
            try {
                if (recognitionRef.current) {
                    // Some browsers expose .abort(); others stop automatically on GC
                    if (typeof recognitionRef.current.abort === "function") recognitionRef.current.abort();
                    recognitionRef.current = null;
                }
            } catch (e) {
                console.warn("Failed to cleanup SpeechRecognition", e);
            }
        };
        // run only once per mount
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Greet when conversationState is upload_video, but only once per mount to avoid duplicate greeting
    useEffect(() => {
        if (conversationState === "upload_video" && !hasGreetedRef.current) {
            hasGreetedRef.current = true;
            addAIMessage("Upload your video to begin editing");
        }
        // run whenever conversationState changes, but the guard prevents duplicate calls
    }, [conversationState]);

    // Play base64 audio returned from server ElevenLabs TTS
    async function playBase64Audio(base64, mime = "audio/mpeg") {
        if (!base64) return;
        const byteString = atob(base64);
        const ab = new ArrayBuffer(byteString.length);
        const ia = new Uint8Array(ab);
        for (let i = 0; i < byteString.length; i += 1) ia[i] = byteString.charCodeAt(i);
        const blob = new Blob([ab], { type: mime });
        const url = URL.createObjectURL(blob);
        const audio = audioRef.current;
        if (!audio) return;
        audio.src = url;
        try {
            await audio.play();
        } catch (err) {
            // autoplay might be blocked; still set the source so user can press play
            console.warn("Playback blocked or failed:", err);
        }
    }

    // Request ElevenLabs TTS for given text via backend
    async function requestServerTTS(text) {
        try {
            // Use relative path so it works in prod where frontend and backend are same origin
            const res = await axios.post("http://localhost:5000/api/tts", { text });
            return res.data; // expects { audio_base64, mime }
        } catch (err) {
            console.error("TTS request failed", err);
            setError("TTS request failed: " + (err?.response?.data?.error || err.message));
            return null;
        }
    }

    // Add an AI message and speak it using server-side ElevenLabs TTS
    async function addAIMessage(text) {
        if (!text) return;
        setMessages((prev) => [...prev, { role: "ai", content: text }]);
        // get backend ElevenLabs audio
        const tts = await requestServerTTS(text);
        if (tts && tts.audio_base64) {
            await playBase64Audio(tts.audio_base64, tts.mime || "audio/mpeg");
        }
    }

    const addUserMessage = (text) => {
        if (!text) return;
        setMessages((prev) => [...prev, { role: "user", content: text }]);
    };

    const startListening = () => {
        if (recognitionRef.current && !listening) {
            try {
                setListening(true);
                recognitionRef.current.start();
            } catch (e) {
                setError("Failed to start speech recognition: " + (e?.message || e));
                setListening(false);
            }
        }
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            const url = URL.createObjectURL(file);
            setHistory([{ blob: file, url }]);
            setPromptHistory([]);
            addUserMessage("Video uploaded");
            addAIMessage("Describe the edits you would like to make");
            setConversationState("get_prompt");
        }
    };

    const handleUserInput = (transcript) => {
        addUserMessage(transcript);
        if (conversationState === "get_prompt") {
            submitEdit(transcript);
        } else if (conversationState === "review") {
            const lowerTranscript = transcript.toLowerCase();
            if (lowerTranscript.includes("restore")) {
                if (history.length > 1) {
                    setHistory((prev) => {
                        const removed = prev[prev.length - 1];
                        try {
                            URL.revokeObjectURL(removed.url);
                        } catch (e) { }
                        return prev.slice(0, -1);
                    });
                    setPromptHistory((prev) => prev.slice(0, -1));
                    addAIMessage("Previous version restored. What would you like to edit next?");
                    setConversationState("get_prompt");
                } else {
                    addAIMessage("No previous version available. What edits would you like?");
                    setConversationState("get_prompt");
                }
            } else if (
                lowerTranscript.includes("edit") ||
                lowerTranscript.includes("change") ||
                lowerTranscript.includes("more") ||
                lowerTranscript.includes("yes")
            ) {
                addAIMessage("What additional edits would you like?");
                setConversationState("get_prompt");
            } else if (lowerTranscript.includes("done") || lowerTranscript.includes("no")) {
                addAIMessage("Session complete. Upload a new video to continue.");
                setConversationState("upload_video");
                setHistory([]);
                setPromptHistory([]);
                setMessages([]);
                hasGreetedRef.current = false; // allow greeting to run again when upload_video state is set and component still mounted
            } else {
                addAIMessage("Please specify: more edits, restore previous version, or done?");
            }
        }
    };

    const submitEdit = async (prompt) => {
        const current = history[history.length - 1];
        if (!current) return;

        setUploading(true);
        setError(null);

        let fullPrompt = prompt;
        if (promptHistory.length > 0) {
            fullPrompt = `Previous edits: ${promptHistory.join(". ")}. Additional edit: ${prompt}`;
        }

        const formData = new FormData();
        formData.append("video", current.blob);
        formData.append("user_prompt", fullPrompt);

        try {
            const response = await fetch("http://localhost:5000/api/edit", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || "Processing failed");
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            setHistory((prev) => [...prev, { blob, url }]);
            setPromptHistory((prev) => [...prev, prompt]);
            addAIMessage("Edit complete. Continue editing, restore previous version, or finish?");
            setConversationState("review");
        } catch (err) {
            console.error(err);
            setError(err.message);
        } finally {
            setUploading(false);
        }
    };

    const handleTextSubmit = () => {
        if (inputText.trim()) {
            handleUserInput(inputText.trim());
            setInputText("");
        }
    };

    const current = history[history.length - 1] || null;

    return (
        <div className="min-h-screen bg-[#f6f0e9]">
            <div className="container mx-auto px-4 py-8">
                <div className="max-w-4xl mx-auto">
                    {/* Header */}
                    <div className="text-center mb-8">
                        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-purple-400 to-purple-600 rounded-2xl mb-4 shadow-lg">
                            <Video className="w-8 h-8 text-white" />
                        </div>
                        <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-700 to-purple-900 bg-clip-text text-transparent">
                            AI Video Editor
                        </h1>
                        <p className="text-purple-700 mt-2 font-medium">Professional video editing for artisans</p>
                    </div>

                    <div className="grid lg:grid-cols-2 gap-8">
                        {/* Chat Interface */}
                        <div className="bg-white/80 backdrop-blur-md rounded-xl shadow-xl border border-purple-200 overflow-hidden">
                            <div className="bg-[#3f3ad3] p-6">
                                <h2 className="text-xl font-semibold text-white flex items-center">
                                    <div className="w-2 h-2 bg-purple-200 rounded-full mr-3 animate-pulse"></div>
                                    Assistant
                                </h2>
                            </div>

                            <div className="h-80 overflow-y-auto p-6 space-y-4">
                                {messages.map((msg, idx) => (
                                    <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                                        <div
                                            className={`max-w-xs lg:max-w-sm px-4 py-3 rounded-2xl ${msg.role === "ai"
                                                ? "bg-gradient-to-r from-purple-50 to-purple-[#3f3ad3] text-[#3f3ad3] border border-purple-200"
                                                : "bg-gradient-to-r from-purple-400 to-purple-500 text-white shadow-md"
                                                }`}
                                        >
                                            <p className="text-sm">{msg.content}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Input Controls */}
                            <div className="p-6 bg-purple-50 border-t border-purple-200">
                                {conversationState === "upload_video" && (
                                    <div className="relative">
                                        <input
                                            type="file"
                                            accept="video/*"
                                            onChange={handleFileChange}
                                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                            id="video-upload"
                                        />
                                        <label
                                            htmlFor="video-upload"
                                            className="flex items-center justify-center w-full py-4 px-6 border-2 border-dashed border-[#3f3ad3] rounded-2xl bg-gradient-to-r from-purple-50 to-purple-100 hover:from-purple-100 hover:to-purple-200 transition-all duration-300 cursor-pointer group"
                                        >
                                            <Upload className="w-6 h-6 text-[#3f3ad3] mr-3 group-hover:scale-110 transition-transform" />
                                            <span className="text-[#3f3ad3] font-medium">Choose Video File</span>
                                        </label>
                                    </div>
                                )}

                                {(conversationState === "get_prompt" || conversationState === "review") && (
                                    <div className="space-y-3">
                                        <button
                                            onClick={() => {
                                                if (recognitionRef.current && !listening) {
                                                    setListening(true);
                                                    recognitionRef.current.start();
                                                }
                                            }}
                                            disabled={listening || uploading}
                                            className={`w-full py-4 px-6 rounded-2xl font-medium transition-all duration-300 flex items-center justify-center shadow-lg ${listening
                                                ? "bg-gradient-to-r from-purple-400 to-purple-500 text-white animate-pulse"
                                                : uploading
                                                    ? "bg-purple-300 text-purple-500 cursor-not-allowed"
                                                    : "bg-gradient-to-r from-purple-500 to-purple-700 text-white hover:from-purple-600 hover:to-purple-800 transform hover:scale-[1.02] active:scale-[0.98]"
                                                }`}
                                        >
                                            {listening ? (
                                                <>
                                                    <MicOff className="w-5 h-5 mr-2" />
                                                    Listening...
                                                </>
                                            ) : uploading ? (
                                                <>
                                                    <div className="w-5 h-5 mr-2 border-2 border-purple-300 border-t-transparent rounded-full animate-spin"></div>
                                                    Processing...
                                                </>
                                            ) : (
                                                <>
                                                    <Mic className="w-5 h-5 mr-2" />
                                                    Voice Input
                                                </>
                                            )}
                                        </button>

                                        <div className="flex space-x-2">
                                            <input
                                                type="text"
                                                value={inputText}
                                                onChange={(e) => setInputText(e.target.value)}
                                                onKeyPress={(e) => e.key === "Enter" && handleTextSubmit()}
                                                className="flex-1 px-4 py-3 border border-purple-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent transition-all duration-200 bg-white/90"
                                                placeholder="Type your instructions..."
                                                disabled={uploading}
                                            />
                                            <button
                                                onClick={handleTextSubmit}
                                                disabled={uploading || !inputText.trim()}
                                                className={`px-6 py-3 rounded-xl font-medium transition-all duration-300 ${uploading || !inputText.trim()
                                                    ? "bg-purple-300 text-purple-500 cursor-not-allowed"
                                                    : "bg-gradient-to-r from-purple-400 to-purple-600 text-white hover:from-purple-500 hover:to-purple-700 shadow-lg transform hover:scale-105 active:scale-95"
                                                    }`}
                                            >
                                                <Send className="w-5 h-5" />
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Video Preview */}
                        <div className="bg-white/80 backdrop-blur-md rounded-xl shadow-xl border border-purple-200 overflow-hidden">
                            <div className="bg-[#a5e1e9] p-6">
                                <h2 className="text-xl font-semibold flex items-center  text-blue-600">
                                    <Video className="w-6 h-6 mr-3" />
                                    Video Preview
                                </h2>
                            </div>

                            <div className="p-6">
                                {current ? (
                                    <div className="space-y-4">
                                        <div className="relative rounded-2xl overflow-hidden shadow-2xl bg-[#a5e1e9]">
                                            <video controls src={current.url} key={current.url} className="w-full h-auto" style={{ maxHeight: "400px" }} />
                                        </div>

                                        {promptHistory.length > 0 && (
                                            <div className="bg-[#a5e1e9] rounded-2xl p-4 border border-purple-200">
                                                <div className="flex items-center mb-3">
                                                    <History className="w-5 h-5 text-purple-600 mr-2" />
                                                    <span className="font-medium text-purple-700">Edit History</span>
                                                </div>
                                                <div className="space-y-2">
                                                    {promptHistory.map((prompt, idx) => (
                                                        <div key={idx} className="flex items-start">
                                                            <div className="w-6 h-6 bg-gradient-to-r from-purple-500 to-purple-600 rounded-full flex items-center justify-center mr-3 mt-0.5 flex-shrink-0">
                                                                <span className="text-white text-xs font-bold">{idx + 1}</span>
                                                            </div>
                                                            <p className="text-sm text-purple-700 leading-relaxed">{prompt}</p>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center justify-center h-80 text-purple-500">
                                        <div className="w-24 h-24 bg-[#a5e1e9] rounded-full flex items-center justify-center mb-4">
                                            <Video className="w-12 h-12 text-blue-600" />
                                        </div>
                                        <p className="text-lg font-medium text-blue-600">No video uploaded</p>
                                        <p className="text-sm text-center mt-2 text-blue-600">Upload a video file to start editing</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Error Display */}
                    {error && (
                        <div className="mt-6 bg-gradient-to-r from-purple-50 to-purple-100 border border-purple-300 rounded-2xl p-4">
                            <div className="flex items-center">
                                <X className="w-5 h-5 text-purple-500 mr-3" />
                                <p className="text-purple-700 font-medium">{error}</p>
                            </div>
                        </div>
                    )}

                    <audio ref={audioRef} className="hidden" />

                    {/* Floating Elements */}
                    <div className="absolute top-10 right-10 w-40 h-40 bg-gradient-to-r from-purple-200 to-purple-300 rounded-full opacity-30 blur-3xl animate-pulse"></div>
                    <div className="absolute bottom-10 left-10 w-32 h-32 bg-gradient-to-r from-purple-300 to-purple-400 rounded-full opacity-30 blur-3xl animate-pulse"></div>
                    <div className="absolute top-1/2 right-1/4 w-28 h-28 bg-gradient-to-r from-purple-200 to-purple-400 rounded-full opacity-25 blur-2xl"></div>
                </div>
            </div>
        </div>
    );
}
