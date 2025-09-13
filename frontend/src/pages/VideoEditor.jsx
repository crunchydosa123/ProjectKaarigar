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

  useEffect(() => {
    // Initialize browser SpeechRecognition for voice input (frontend)
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

    // When arriving at upload page, greet using ElevenLabs TTS
    if (conversationState === "upload_video") {
      addAIMessage("Upload your video to begin editing");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

    // We'll decide inside the functional updater whether to add.
    let shouldAdd = true;

    setMessages((prev) => {
      const last = prev[prev.length - 1];
      // Compare trimmed text to avoid false negatives from extra whitespace
      if (last && last.role === "ai" && last.content.trim() === text.trim()) {
        shouldAdd = false;
        return prev; // return unchanged array — no duplicate added
      }
      return [...prev, { role: "ai", content: text }];
    });

    if (!shouldAdd) {
      // Optional: log for debugging
      console.debug("addAIMessage: duplicate AI message skipped");
      return;
    }

    // If we added the message, request TTS and play it.
    try {
      const tts = await requestServerTTS(text);
      if (tts && tts.audio_base64) {
        await playBase64Audio(tts.audio_base64, tts.mime || "audio/mpeg");
      }
    } catch (e) {
      console.error("addAIMessage: TTS/playback failed", e);
      // requestServerTTS already sets error in your original code, so no extra setError required,
      // but you can set one here if you'd like:
      // setError("TTS request failed: " + (e?.message || e));
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