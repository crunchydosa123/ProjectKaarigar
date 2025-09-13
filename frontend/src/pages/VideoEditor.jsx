import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import { Upload, Mic, MicOff, Send, X, ArrowLeft, RotateCw, Stars } from "lucide-react";
import MenuDrawer from "../components/MenuDrawer";

// Mobile-first single-file video editor UI
// - Fullscreen video on mobile
// - Floating Prompt FAB opens a bottom-sheet for voice/text prompts
// - Keeps original logic for uploading, editing, history, TTS and SpeechRecognition

export default function MobileVideoEditor() {
  const [messages, setMessages] = useState([]);
  const [conversationState, setConversationState] = useState("upload_video");
  const [history, setHistory] = useState([]); // { blob, url }
  const [promptHistory, setPromptHistory] = useState([]);
  const [listening, setListening] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [inputText, setInputText] = useState("");
  const [sheetOpen, setSheetOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  const recognitionRef = useRef(null);
  const audioRef = useRef(null);

  // Initialize SpeechRecognition
  useEffect(() => {
    if ("SpeechRecognition" in window || "webkitSpeechRecognition" in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript.trim();
        setListening(false);
        handleUserInput(transcript);
      };
      recognitionRef.current.onend = () => setListening(false);
      recognitionRef.current.onerror = (e) => {
        setError(`Speech recognition error: ${e.message}`);
        setListening(false);
      };
    }

    // greet when arriving to upload state
    if (conversationState === "upload_video") {
      addAIMessage("Tap to upload a video to begin editing.");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationState]);

  // TTS: play base64 audio
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
      console.warn("Playback blocked or failed:", err);
    }
  }

  async function requestServerTTS(text) {
    try {
      const res = await axios.post("http://localhost:5000/api/tts", { text });
      return res.data; // expects { audio_base64, mime }
    } catch (err) {
      console.error("TTS request failed", err);
      setError("TTS request failed: " + (err?.response?.data?.error || err.message));
      return null;
    }
  }

  // Adds AI message and speaks it. Prevents duplicate final text messages.
  async function addAIMessage(text) {
    if (!text) return;
    let shouldAdd = true;
    setMessages((prev) => {
      const last = prev[prev.length - 1];
      if (last && last.role === "ai" && last.content.trim() === text.trim()) {
        shouldAdd = false;
        return prev;
      }
      return [...prev, { role: "ai", content: text }];
    });

    if (!shouldAdd) return;

    try {
      const tts = await requestServerTTS(text);
      if (tts && tts.audio_base64) {
        await playBase64Audio(tts.audio_base64, tts.mime || "audio/mpeg");
      }
    } catch (e) {
      console.error("addAIMessage: TTS/playback failed", e);
    }
  }

  const addUserMessage = (text) => {
    if (!text) return;
    setMessages((prev) => [...prev, { role: "user", content: text }]);
  };

  const startListening = () => {
    if (recognitionRef.current && !listening) {
      setListening(true);
      recognitionRef.current.start();
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
            try { URL.revokeObjectURL(removed.url); } catch (e) { }
            return prev.slice(0, -1);
          });
          setPromptHistory((prev) => prev.slice(0, -1));
          addAIMessage("Previous version restored. What would you like to edit next?");
          setConversationState("get_prompt");
        } else {
          addAIMessage("No previous version available. What edits would you like?");
          setConversationState("get_prompt");
        }
      } else if (lowerTranscript.includes("edit") || lowerTranscript.includes("change") || lowerTranscript.includes("more") || lowerTranscript.includes("yes")) {
        addAIMessage("What additional edits would you like?");
        setConversationState("get_prompt");
      } else if (lowerTranscript.includes("done") || lowerTranscript.includes("no")) {
        addAIMessage("Session complete. Upload a new video to continue.");
        setConversationState("upload_video");
        setHistory([]);
        setPromptHistory([]);
        setMessages([]);
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
      fullPrompt = `Previous edits: ${promptHistory.join('. ')}. Additional edit: ${prompt}`;
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
      setSheetOpen(false);
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

  // UI helpers
  const openSheetForPrompt = () => {
    if (!current) {
      // open upload instead
      document.getElementById("mobile-upload").click();
      return;
    }
    setSheetOpen(true);
  };

  const restorePrevious = () => {
    if (history.length > 1) {
      setHistory((prev) => {
        const removed = prev[prev.length - 1];
        try { URL.revokeObjectURL(removed.url); } catch (e) { }
        return prev.slice(0, -1);
      });
      setPromptHistory((prev) => prev.slice(0, -1));
      addAIMessage("Previous version restored. What would you like to edit next?");
      setConversationState("get_prompt");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-100 via-blue-50 to-pink-100 overflow-hidden relative">
      {/* Floating background blobs */}
      <div className="absolute top-10 left-10 transform -translate-x-1/2 w-72 h-72 bg-gradient-to-br from-purple-300 to-pink-300 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse md:transform-none" />
      <div className="absolute top-20 right-10 w-64 h-64 bg-gradient-to-br from-blue-300 to-purple-300 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse delay-1000 hidden md:block" />
      <div className="absolute bottom-10 left-1/2 w-80 h-80 bg-gradient-to-br from-pink-300 to-blue-300 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse delay-2000" />

      <button
        onClick={() => setMenuOpen(true)}
        className="absolute top-4 left-4 z-20 cursor-pointer"
        aria-label="Open menu"
      >
        <svg className="w-8 h-8 text-gray-800" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Fullscreen video area */}
      <div className="fixed inset-0 flex items-center justify-center">
        {current ? (
          <video
            controls
            playsInline
            src={current.url}
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center p-6 relative z-10">
            <div className="w-28 h-28 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full flex items-center justify-center mb-6 shadow-lg">
              <Upload className="w-12 h-12 text-white" />
            </div>
            <p className="text-lg font-medium mb-2 text-gray-700">No video uploaded</p>
            <p className="text-sm opacity-80 mb-6 text-center text-gray-600">
              Tap the button below to upload a video and start editing
            </p>
            <label
              htmlFor="mobile-upload"
              className="px-6 py-3 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 text-white font-medium cursor-pointer shadow-md hover:scale-105 transition-transform"
            >
              Choose video
            </label>
            <input id="mobile-upload" type="file" accept="video/*" onChange={handleFileChange} className="hidden" />
          </div>
        )}
      </div>

      {/* Floating FAB */}
      <div className="fixed left-0 right-0 bottom-6 flex items-center justify-center pointer-events-none z-20">
        <button
          onClick={openSheetForPrompt}
          className="pointer-events-auto inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 shadow-xl text-white font-bold transform hover:scale-105 active:scale-95"
          aria-label="Open prompt"
        >
          <Stars className="w-10 h-10" />
        </button>
      </div>

      {/* Bottom Sheet */}
      <div
        className={`fixed left-0 right-0 bottom-0 z-50 transition-transform duration-300 ${sheetOpen ? "translate-y-0" : "translate-y-full"
          }`}
        aria-hidden={!sheetOpen}
      >
        <div className="max-w-xl mx-auto bg-white/80 backdrop-blur-xl rounded-t-3xl shadow-2xl p-4 text-black">
          <div className="flex items-center justify-between mb-3">
            <div className="text-lg font-semibold">Assistant</div>
            <div className="flex items-center gap-2">
              {history.length > 1 && (
                <button onClick={restorePrevious} className="px-3 py-2 rounded-lg bg-purple-100 text-purple-700 text-sm">Restore</button>
              )}
              <button aria-label="Close" onClick={() => setSheetOpen(false)} className="p-2 rounded-lg">
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Messages preview (compact) */}
          <div className="h-32 overflow-y-auto mb-3 p-2 bg-gray-50 rounded-lg">
            {messages.length === 0 ? (
              <div className="text-gray-500 text-sm">No messages yet — use voice or type to talk to the assistant.</div>
            ) : (
              messages.slice(-6).map((m, i) => (
                <div key={i} className={`mb-2 text-sm ${m.role === 'ai' ? 'text-purple-700' : 'text-gray-800 text-right'}`}>
                  {m.content}
                </div>
              ))
            )}
          </div>

          {/* Prompt input / voice controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                if (recognitionRef.current && !listening) {
                  setListening(true);
                  recognitionRef.current.start();
                } else {
                  startListening();
                }
              }}
              className={`p-3 rounded-xl flex items-center justify-center border ${listening ? 'bg-red-100 border-red-200' : 'bg-white border-gray-200'}`}
              aria-label="Voice input"
            >
              {listening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </button>

            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleTextSubmit()}
              placeholder={uploading ? 'Processing...' : 'Describe the edit you want...'}
              className="flex-1 px-4 py-3 rounded-xl border border-gray-200 focus:outline-none"
              disabled={uploading}
            />

            <button
              onClick={handleTextSubmit}
              disabled={uploading || !inputText.trim()}
              className={`p-3 rounded-xl ${uploading || !inputText.trim() ? 'bg-gray-200 text-gray-400' : 'bg-purple-600 text-white'}`}
              aria-label="Send"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>

          {/* Prompt history list */}
          {promptHistory.length > 0 && (
            <div className="mt-3 p-2 bg-gray-50 rounded-lg text-sm">
              <div className="font-medium mb-2">Edit History</div>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {promptHistory.map((p, idx) => (
                  <div key={idx} className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white text-xs">{idx + 1}</div>
                    <div className="text-sm text-gray-800">{p}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Error display */}
          {error && (
            <div className="mt-3 p-3 rounded-lg bg-red-50 text-red-700 text-sm">{error}</div>
          )}

          <audio ref={audioRef} className="hidden" />
        </div>
      </div>
      <MenuDrawer open={menuOpen} onClose={() => setMenuOpen(false)} />
    </div>
  );
}
