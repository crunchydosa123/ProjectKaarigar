import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import { X } from "lucide-react";
import "../index.css";

import VideoHeader from "../components/VideoHeader";
import ChatWindow from "../components/ChatWindow";
import EditorControls from "../components/EditorControls";
import VideoPreview from "../components/VideoPreview";
import MenuDrawer from "../components/MenuDrawer";

export default function VideoEditor() {
  const [messages, setMessages] = useState([]);
  const [conversationState, setConversationState] = useState("upload_video");
  const [history, setHistory] = useState([]);
  const [promptHistory, setPromptHistory] = useState([]);
  const [listening, setListening] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [inputText, setInputText] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);

  const recognitionRef = useRef(null);
  const audioRef = useRef(null); // for playing TTS audio
  const hasGreetedRef = useRef(false);

  // SpeechRecognition init
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
          console.warn("Recognition parse error", e);
        }
      };

      recog.onend = () => setListening(false);
      recog.onerror = (e) => {
        setError(`Speech recognition error: ${e?.message || e}`);
        setListening(false);
      };

      recognitionRef.current = recog;
    }

    return () => {
      try {
        if (recognitionRef.current && typeof recognitionRef.current.abort === "function") {
          recognitionRef.current.abort();
        }
        recognitionRef.current = null;
      } catch (e) {
        console.warn("cleanup error", e);
      }
    };
  }, []);

  // greet once (same behavior as Conversational)
  useEffect(() => {
    if (conversationState === "upload_video" && !hasGreetedRef.current) {
      hasGreetedRef.current = true;
      addAIMessage("Upload your video to begin editing");
    }
  }, [conversationState]);

  // Play base64 audio
  async function playBase64Audio(base64, mime = "audio/mpeg") {
    if (!base64) return;
    try {
      const byteString = atob(base64);
      const ab = new ArrayBuffer(byteString.length);
      const ia = new Uint8Array(ab);
      for (let i = 0; i < byteString.length; i++) ia[i] = byteString.charCodeAt(i);
      const blob = new Blob([ab], { type: mime });
      const url = URL.createObjectURL(blob);
      const audio = audioRef.current;
      if (!audio) return;
      audio.src = url;
      await audio.play().catch((e) => {
        console.warn("Playback blocked:", e);
      });
    } catch (e) {
      console.error("playBase64Audio error", e);
    }
  }

  // TTS request
  async function requestServerTTS(text) {
    try {
      const res = await axios.post("http://localhost:5000/api/tts", { text });
      return res.data;
    } catch (err) {
      console.error("TTS request failed", err);
      setError("TTS request failed: " + (err?.response?.data?.error || err.message));
      return null;
    }
  }

  // Add AI message + speak
  async function addAIMessage(text) {
    if (!text) return;
    setMessages((prev) => [...prev, { role: "ai", content: text }]);
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
    const file = e.target.files?.[0];
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
      const lower = transcript.toLowerCase();
      if (lower.includes("restore")) {
        if (history.length > 1) {
          setHistory((prev) => {
            const removed = prev[prev.length - 1];
            try { URL.revokeObjectURL(removed.url); } catch (e) {}
            return prev.slice(0, -1);
          });
          setPromptHistory((prev) => prev.slice(0, -1));
          addAIMessage("Previous version restored. What would you like to edit next?");
          setConversationState("get_prompt");
        } else {
          addAIMessage("No previous version available. What edits would you like?");
          setConversationState("get_prompt");
        }
      } else if (["edit", "change", "more", "yes"].some(k => lower.includes(k))) {
        addAIMessage("What additional edits would you like?");
        setConversationState("get_prompt");
      } else if (lower.includes("done") || lower.includes("no")) {
        addAIMessage("Session complete. Upload a new video to continue.");
        setConversationState("upload_video");
        setHistory([]); setPromptHistory([]); setMessages([]);
        hasGreetedRef.current = false;
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

    const fd = new FormData();
    fd.append("video", current.blob);
    fd.append("user_prompt", fullPrompt);

    try {
      const response = await fetch("http://localhost:5000/api/edit", {
        method: "POST",
        body: fd
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || "Processing failed");
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
    <div className="min-h-screen bg-gradient-to-br from-purple-100 via-purple-50 to-pink-100 overflow-hidden relative">
      {/* Floating background blobs (soft purple/pink) */}
      <div className="absolute top-10 left-10 transform -translate-x-1/2 w-72 h-72 bg-gradient-to-br from-purple-300 to-pink-300 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse md:transform-none" />
      <div className="absolute top-20 right-10 w-64 h-64 bg-gradient-to-br from-purple-300 to-purple-400 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse delay-1000 hidden md:block" />
      <div className="absolute bottom-10 left-1/2 w-80 h-80 bg-gradient-to-br from-pink-300 to-purple-300 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse delay-2000" />

      {/* Hamburger */}
      <button
        onClick={() => setMenuOpen(true)}
        className="absolute top-4 left-4 z-20 cursor-pointer"
        aria-label="Open menu"
      >
        <svg className="w-8 h-8 text-gray-800" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Main content */}
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-5xl mx-auto relative">
          <VideoHeader />

          <div className="grid lg:grid-cols-2 gap-8 mt-6">
            {/* Left: Chat + Controls */}
            <div className="bg-white/80 backdrop-blur-md rounded-xl shadow-2xl border border-purple-200 overflow-hidden">
              <div className="bg-gradient-to-r from-purple-200 to-pink-200 p-6">
                <h2 className="text-xl font-semibold flex items-center text-purple-700">
                  <div className="w-2 h-2 bg-pink-100 rounded-full mr-3 animate-pulse" />
                  Assistant
                </h2>
              </div>

              <ChatWindow messages={messages} />

              <div className="p-6 bg-purple-50 border-t border-purple-200">
                <EditorControls
                  conversationState={conversationState}
                  recognitionRef={recognitionRef}
                  listening={listening}
                  setListening={setListening}
                  uploading={uploading}
                  inputText={inputText}
                  setInputText={setInputText}
                  startListening={startListening}
                  handleFileChange={handleFileChange}
                  handleTextSubmit={handleTextSubmit}
                />
              </div>
            </div>

            {/* Right: Video preview */}
            <VideoPreview current={current} promptHistory={promptHistory} />
          </div>

          {/* Error box (styled to match Conversational) */}
          {error && (
            <div className="mt-6 bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-300 rounded-2xl p-4">
              <div className="flex items-center">
                <X className="w-5 h-5 text-purple-500 mr-3" />
                <p className="text-purple-700 font-medium">{error}</p>
              </div>
            </div>
          )}

          <audio ref={audioRef} className="hidden" />

          {/* Floating accent elements */}
          <div className="absolute top-10 right-10 w-40 h-40 bg-gradient-to-r from-purple-200 to-pink-200 rounded-full opacity-30 blur-3xl animate-pulse" />
          <div className="absolute bottom-10 left-10 w-32 h-32 bg-gradient-to-r from-purple-300 to-pink-200 rounded-full opacity-30 blur-3xl animate-pulse" />
          <div className="absolute top-1/2 right-1/4 w-28 h-28 bg-gradient-to-r from-purple-200 to-pink-200 rounded-full opacity-25 blur-2xl" />
        </div>
      </div>

      <MenuDrawer open={menuOpen} onClose={() => setMenuOpen(false)} />
    </div>
  );
}
