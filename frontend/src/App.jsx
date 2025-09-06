// src/App.jsx
import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import "./index.css";

/**
 * Updated Artisan Conversation widget (audio-first) with improved recording:
 * - Auto-stop recording only after sustained silence is detected (reduces cuts).
 * - Manual start/stop still supported.
 * - Max recording length enforced.
 * - Plays prompt from backend, uploads recorded blob to /api/converse/submit_audio
 */

export default function App() {
  const [status, setStatus] = useState("idle"); // idle | playing_prompt | ready_record | recording | uploading
  const [transcript, setTranscript] = useState("");
  const [assistantText, setAssistantText] = useState("");
  const [history, setHistory] = useState([]); // {role, text}
  const [error, setError] = useState(null);

  const audioElRef = useRef(null);

  // Recording & VAD state refs (persist across renders)
  const mediaStreamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const recordedChunksRef = useRef([]);
  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const sourceRef = useRef(null);
  const vadIntervalRef = useRef(null);
  const silenceStartRef = useRef(null);
  const timeoutStopRef = useRef(null);

  // Config (tweak to taste)
  const VAD_CHECK_INTERVAL_MS = 100;        // how often to sample audio level
  const SILENCE_THRESHOLD = 0.01;           // RMS threshold; lower -> more sensitive to silence
  const SILENCE_DETECT_MS = 1800;            // require this many ms of sustained silence to auto-stop
  const RECORDING_TAIL_MS = 300;            // add a tiny tail after silence to avoid chopping
  const MAX_RECORDING_MS = 100_000;          // hard max (90s)

  // Play base64 audio and return a promise that resolves when playback ends
  function playBase64Audio(base64, mime = "audio/mpeg") {
    return new Promise((resolve, reject) => {
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
        // autoplay / user gesture restrictions may block play(); still resolve so UI continues
        console.warn("Playback may be blocked:", e);
        resolve();
      });
    });
  }

  // Start flow: request multilingual TTS prompt
  async function handleStartCallTypes() {
    setError(null);
    setAssistantText("");
    setTranscript("");
    setStatus("playing_prompt");
    try {
      const res = await axios.get("http://localhost:5000/api/converse/start_language");
      const data = res.data;
      if (data.audio_base64) {
        await playBase64Audio(data.audio_base64, data.mime || "audio/mpeg");
      }
      // after prompt finishes, enable recording
      setStatus("ready_record");
    } catch (e) {
      console.error(e);
      setError(e?.response?.data?.error || e.message);
      setStatus("idle");
    }
  }

  // Utility: cleanup audio analysis and streams
  function cleanupRecordingResources() {
    // stop VAD interval
    if (vadIntervalRef.current) {
      clearInterval(vadIntervalRef.current);
      vadIntervalRef.current = null;
    }
    // stop timeout stop
    if (timeoutStopRef.current) {
      clearTimeout(timeoutStopRef.current);
      timeoutStopRef.current = null;
    }
    // close audio context
    if (audioCtxRef.current) {
      try {
        audioCtxRef.current.close();
      } catch (e) { }
      audioCtxRef.current = null;
    }
    // disconnect source/analyser
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
    // stop media tracks
    if (mediaStreamRef.current) {
      try {
        mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      } catch (e) { }
      mediaStreamRef.current = null;
    }
  }

  // Start recording with VAD (Voice Activity Detection)
  async function startRecording() {
    setError(null);

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setError("Microphone not supported in this browser.");
      return;
    }

    try {
      // request mic
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      // create MediaRecorder
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
        // set a hard max stop to avoid runaway recordings
        timeoutStopRef.current = setTimeout(() => {
          // stop due to max length
          stopRecording();
        }, MAX_RECORDING_MS);
      };

      // We'll stop recorder ourselves when VAD detects silence
      mr.start(250); // timeslice to get regular dataavailable events

      // Create AudioContext + analyser for level monitoring
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      audioCtxRef.current = audioCtx;
      const source = audioCtx.createMediaStreamSource(stream);
      sourceRef.current = source;
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 2048;
      analyserRef.current = analyser;

      source.connect(analyser);

      const dataArray = new Float32Array(analyser.fftSize);

      // Reset silence detection
      silenceStartRef.current = null;

      // VAD poller - checks amplitude every VAD_CHECK_INTERVAL_MS
      vadIntervalRef.current = setInterval(() => {
        try {
          analyser.getFloatTimeDomainData(dataArray);
          // compute RMS
          let sumSquares = 0;
          for (let i = 0; i < dataArray.length; i++) {
            const v = dataArray[i];
            sumSquares += v * v;
          }
          const rms = Math.sqrt(sumSquares / dataArray.length);
          // console.debug("rms", rms);

          if (rms < SILENCE_THRESHOLD) {
            // below threshold => possible silence
            if (silenceStartRef.current == null) {
              silenceStartRef.current = Date.now();
            } else {
              const elapsed = Date.now() - silenceStartRef.current;
              if (elapsed >= SILENCE_DETECT_MS) {
                // we've seen sustained silence; stop with a small tail
                // add a tiny tail to avoid chopping
                setTimeout(() => {
                  // guard: ensure recorder still active
                  if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
                    stopRecording();
                  }
                }, RECORDING_TAIL_MS);
                // clear interval early so we don't queue repeated stops
                clearInterval(vadIntervalRef.current);
                vadIntervalRef.current = null;
              }
            }
          } else {
            // speech detected, reset silence timer
            silenceStartRef.current = null;
          }
        } catch (e) {
          console.warn("VAD error", e);
        }
      }, VAD_CHECK_INTERVAL_MS);
    } catch (e) {
      console.error(e);
      setError("Microphone permission denied or error: " + (e?.message || e));
      stopRecordingImmediate();
    }
  }

  // Stop recording gracefully (will trigger MediaRecorder.onstop)
  function stopRecording() {
    // Stop VAD interval to avoid duplicate actions
    if (vadIntervalRef.current) {
      clearInterval(vadIntervalRef.current);
      vadIntervalRef.current = null;
    }
    // Clear max timeout
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
      // nothing to stop, still attempt cleanup
      stopRecordingImmediate();
    }

    // When recorder stops it will not necessarily call onstop in all browsers reliably in this wrapper,
    // so we do a small delay then finish the process (but prefer onstop if available).
    // We'll set a short timer to finalize if onstop hasn't fired.
    setTimeout(() => {
      finalizeRecordingAndUpload();
    }, 400);
  }

  // Force-stop and cleanup (use for errors)
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

  // Called after recorder has been stopped; build blob and upload
  async function finalizeRecordingAndUpload() {
    try {
      setStatus("uploading");
      // collect recorded data
      const pieces = recordedChunksRef.current || [];
      if (!pieces || pieces.length === 0) {
        // nothing recorded
        setStatus("ready_record");
        return;
      }
      const blob = new Blob(pieces, { type: "audio/webm" });
      // cleanup audio resources now
      cleanupRecordingResources();
      mediaRecorderRef.current = null;
      recordedChunksRef.current = [];
      // upload
      await uploadAudioBlob(blob);
    } catch (e) {
      console.error(e);
      setError("Upload error: " + (e?.message || e));
      cleanupRecordingResources();
      setStatus("ready_record");
    }
  }

  // Upload the audio blob to backend STT->Gemini
  async function uploadAudioBlob(blob) {
    setError(null);
    setStatus("uploading");
    const fd = new FormData();
    fd.append("audio", blob, "reply.webm");
    fd.append("history", JSON.stringify(history || []));

    try {
      const res = await axios.post("http://localhost:5000/api/converse/submit_audio", fd, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 120000
      });
      const data = res.data;
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
      setError(e?.response?.data?.error || e.message || "Unknown upload error");
    } finally {
      setStatus("ready_record");
    }
  }

  // UI toggle for manual start/stop
  function handleMicToggle() {
    if (status === "ready_record" || status === "idle") {
      startRecording();
    } else if (status === "recording") {
      stopRecording();
    } else {
      // ignore other states
    }
  }

  // Clean up on unmount
  useEffect(() => {
    return () => {
      cleanupRecordingResources();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Render UI (ElevenLabs-like design)
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 flex items-start justify-center p-8">
      <div className="w-full max-w-2xl">
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          <div className="p-6 bg-gradient-to-r from-purple-600 to-indigo-600 text-white">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-xl font-semibold">Artisan Interview</h1>
                <p className="text-sm opacity-90">Audio-first, localized — avoid mid-speech cutoffs.</p>
              </div>
              <div className="text-xs bg-white/20 px-3 py-1 rounded-full">Audio Interview</div>
            </div>
          </div>

          <div className="p-6 space-y-4">
            <div className="flex gap-3 items-center">
              <button
                className="px-4 py-2 rounded-lg bg-white border shadow-sm hover:shadow-md text-sm font-medium"
                onClick={handleStartCallTypes}
                disabled={status === "playing_prompt" || status === "recording"}
              >
                Start Call Types
              </button>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleMicToggle}
                  className={`w-16 h-16 flex items-center justify-center rounded-full shadow-lg text-white ${status === "recording" ? "bg-red-500 animate-pulse" : "bg-gradient-to-br from-red-500 to-pink-500"}`}
                  aria-label="Record reply"
                >
                  {status === "recording" ? (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-7 w-7" fill="currentColor" viewBox="0 0 24 24"><path d="M12 14a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3z" /><path d="M19 11a1 1 0 1 0-2 0 5 5 0 0 1-10 0 1 1 0 1 0-2 0 5 5 0 0 0 4.5 4.97V20H8a1 1 0 1 0 0 2h8a1 1 0 1 0 0-2h-3.5v-4.03A5 5 0 0 0 19 11z" /></svg>
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-7 w-7" fill="currentColor" viewBox="0 0 24 24"><path d="M12 14a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3z" /><path d="M19 11a1 1 0 1 0-2 0 5 5 0 0 1-10 0 1 1 0 1 0-2 0 5 5 0 0 0 4.5 4.97V20H8a1 1 0 1 0 0 2h8a1 1 0 1 0 0-2h-3.5v-4.03A5 5 0 0 0 19 11z" /></svg>
                  )}
                </button>

                <div>
                  <div className="text-xs text-gray-500">Status</div>
                  <div className="text-sm font-medium">
                    {status === "idle" && "Idle"}
                    {status === "playing_prompt" && "Playing prompt..."}
                    {status === "ready_record" && "Ready — press to record"}
                    {status === "recording" && "Recording... (auto-stop on silence)"}
                    {status === "uploading" && "Uploading / processing..."}
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-md p-3">
              <div className="text-xs text-gray-500">Latest transcript (from STT)</div>
              <div className="mt-2 text-sm text-gray-800 min-h-[40px]">{transcript || <span className="text-gray-400">No transcript yet</span>}</div>
            </div>

            <div className="bg-white rounded-md p-3 border">
              <div className="text-xs text-gray-500">Assistant reply</div>
              <div className="mt-2 text-sm text-gray-800 min-h-[40px]">{assistantText || <span className="text-gray-400">No reply yet</span>}</div>
              <audio ref={audioElRef} controls className="mt-3 w-full" />
            </div>

            <div className="text-sm text-gray-600">
              Tip: Allow the mic permission. Speak naturally — the system will wait until you stop speaking for ~{SILENCE_DETECT_MS}ms before sending.
            </div>

            {error && <div className="text-red-600 text-sm">{error}</div>}

            <div>
              <h4 className="text-sm font-medium mb-2">Local conversation history</h4>
              <div className="space-y-2">
                {history.length === 0 && <div className="text-xs text-gray-400">No conversation yet</div>}
                {history.map((m, i) => (
                  <div key={i} className={`p-2 rounded ${m.role === "user" ? "bg-indigo-50" : "bg-green-50"}`}>
                    <div className="text-xs text-gray-500">{m.role}</div>
                    <div className="text-sm">{m.text}</div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        </div>

        <div className="mt-4 text-xs text-gray-500">Backend must have GEMINI_API_KEY and ELEVENLABS_API_KEY configured.</div>
      </div>
    </div>
  );
}
