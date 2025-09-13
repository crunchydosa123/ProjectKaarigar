import React, { useState, useRef, useEffect } from "react";
import "../index.css";

import Header from "../components/Header";
import MicButton from "../components/MicButton";
import StatusText from "../components/StatusText";
import ErrorBox from "../components/ErrorBox";
import TranscriptOverlay from "../components/TranscriptOverlay";
import MenuDrawer from "../components/MenuDrawer";

export default function Conversational() {
  const [status, setStatus] = useState("idle");
  const [transcript, setTranscript] = useState("");
  const [assistantText, setAssistantText] = useState("");
  const [history, setHistory] = useState([]);
  const [error, setError] = useState(null);
  const [showTranscript, setShowTranscript] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

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
        for (let i = 0; i < byteString.length; i++)
          ia[i] = byteString.charCodeAt(i);
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
      } catch (e) {}
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
    } catch (e) {}
    if (mediaStreamRef.current) {
      try {
        mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      } catch (e) {}
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
                  if (
                    mediaRecorderRef.current &&
                    mediaRecorderRef.current.state === "recording"
                  ) {
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
      if (
        mediaRecorderRef.current &&
        (mediaRecorderRef.current.state === "recording" ||
          mediaRecorderRef.current.state === "paused")
      ) {
        try {
          mediaRecorderRef.current.stop();
        } catch (e) {}
      }
    } catch (e) {}
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
        body: fd,
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
      <div className="absolute top-10 left-10 transform -translate-x-1/2 w-72 h-72 bg-gradient-to-br from-purple-300 to-pink-300 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse md:transform-none" />
      <div className="absolute top-20 right-10 w-64 h-64 bg-gradient-to-br from-blue-300 to-purple-300 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse delay-1000 hidden md:block" />
      <div className="absolute bottom-10 left-1/2 w-80 h-80 bg-gradient-to-br from-pink-300 to-blue-300 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse delay-2000" />

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

      {/* Main */}
      <div className="flex flex-col items-center justify-center min-h-screen p-8">
        <div className="text-center space-y-8 relative z-10 w-full max-w-lg">
          <Header />
          <MicButton
            status={status}
            onClick={status !== "idle" ? handleMicToggle : handleStartCallTypes}
          />
          <StatusText status={status} />
          <ErrorBox error={error} />

          {/* Bottom actions */}
          <div className="flex items-center justify-center space-x-4 pt-6">
            <button
              onClick={toggleTranscript}
              className="bg-white/80 backdrop-blur-sm rounded-2xl px-6 py-3 shadow-lg hover:shadow-xl transition-all duration-300 border border-white/30 flex items-center space-x-2"
            >
              <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <span className="text-gray-700 font-medium">View Conversation</span>
            </button>
          </div>

          <audio ref={audioElRef} className="hidden" />
        </div>
      </div>

      {/* Overlay + Drawer */}
      <TranscriptOverlay
        show={showTranscript}
        onClose={toggleTranscript}
        history={history}
      />
      <MenuDrawer open={menuOpen} onClose={() => setMenuOpen(false)} />
    </div>
  );
}
