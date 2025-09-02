// src/App.jsx
import React, { useState, useRef } from "react";

export default function App() {
  const [agentId, setAgentId] = useState("agent_6701k435cqn6f9k8r6krwnd7ym92");
  const [voiceId, setVoiceId] = useState("");
  const [messages, setMessages] = useState([]);
  const [recording, setRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const lastBlobRef = useRef(null);
  const audioRef = useRef(null);
  const [textInput, setTextInput] = useState("");
  const [loading, setLoading] = useState(false);

  const startRecording = async () => {
    setMessages(prev => [...prev, { role: "system", text: "Listening..." }]);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Choose a mimeType that your browser supports
      const options = { mimeType: "audio/webm;codecs=opus" };
      let mediaRecorder;
      try {
        mediaRecorder = new MediaRecorder(stream, options);
      } catch (e) {
        // fallback with default constructor
        mediaRecorder = new MediaRecorder(stream);
      }

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        // create blob from chunks and save to lastBlobRef for debug
        const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        lastBlobRef.current = blob;
        // Record debug message with blob size
        setMessages(prev => [...prev, { role: "system", text: `Recorded ${blob.size} bytes` }]);
        await uploadAudio(blob);
      };

      mediaRecorder.start();
      setRecording(true);
    } catch (err) {
      console.error("microphone error:", err);
      alert("Microphone not accessible. Allow microphone permissions.");
    }
  };

  const stopRecording = () => {
    const mr = mediaRecorderRef.current;
    if (!mr) return;
    // Request last data chunk before stopping to ensure final chunk is emitted
    try {
      if (typeof mr.requestData === "function") {
        mr.requestData();
      }
    } catch (e) {
      // ignore if not supported
      console.warn("requestData failed:", e);
    }
    if (mr.state !== "inactive") {
      mr.stop();
    }
    setRecording(false);
  };

  async function uploadAudio(blob) {
    if (!agentId) {
      alert("Agent ID is required. Paste your agent id in the Agent ID field.");
      return;
    }

    // quick client-side validation
    if (!blob || blob.size === 0) {
      alert("Recorded blob is empty. Try again or check browser support for MediaRecorder.");
      return;
    }

    setLoading(true);
    setMessages(prev => prev.filter(m => m.role !== "system"));
    setMessages(prev => [...prev, { role: "user", text: "… (audio sent)" }]);

    const fd = new FormData();
    // Use a filename with correct extension so server can attempt correct handling
    fd.append("audio", blob, "recording.webm");
    fd.append("agent_id", agentId);
    if (voiceId) fd.append("voice_id", voiceId);

    // For debugging, add blob size as a field (optional)
    fd.append("client_blob_size", String(blob.size));

    try {
      const res = await fetch("http://localhost:5000/api/conv/audio", {
        method: "POST",
        body: fd
      });

      const data = await res.json();
      if (!res.ok) {
        console.error("Server response (error):", data);
        alert("Server error: " + (data.error || JSON.stringify(data)));
        setLoading(false);
        return;
      }

      const transcript = data.transcript;
      const reply = data.reply_text;
      if (transcript) setMessages(prev => [...prev, { role: "user", text: transcript }]);
      if (reply) setMessages(prev => [...prev, { role: "agent", text: reply }]);

      if (data.audio_base64) {
        const audioEl = audioRef.current;
        audioEl.src = "data:audio/mpeg;base64," + data.audio_base64;
        audioEl.play().catch(() => { });
      } else if (data.note) {
        setMessages(prev => [...prev, { role: "system", text: data.note }]);
      }

      // optional: show uploaded_file diagnostics
      if (data.uploaded_file) {
        setMessages(prev => [...prev, { role: "system", text: `Server received file ${data.uploaded_file.filename} (${data.uploaded_file.size_bytes} bytes)` }]);
      }
    } catch (err) {
      console.error("Network/upload error:", err);
      alert("Network or server error.");
    } finally {
      setLoading(false);
    }
  }

  async function sendText(e) {
    e.preventDefault();
    if (!textInput.trim()) return;
    if (!agentId) {
      alert("Agent ID is required. Paste your agent id in the Agent ID field.");
      return;
    }
    setLoading(true);
    const thisText = textInput.trim();
    setMessages(prev => [...prev, { role: "user", text: thisText }]);
    setTextInput("");

    try {
      const res = await fetch("http://localhost:5000/api/conv/text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: thisText, agent_id: agentId, voice_id: voiceId || undefined })
      });
      const data = await res.json();
      if (!res.ok) {
        alert("Server error: " + (data.error || JSON.stringify(data)));
        setLoading(false);
        return;
      }
      if (data.reply_text) setMessages(prev => [...prev, { role: "agent", text: data.reply_text }]);
      if (data.audio_base64) {
        const audioEl = audioRef.current;
        audioEl.src = "data:audio/mpeg;base64," + data.audio_base64;
        audioEl.play().catch(() => { });
      } else if (data.note) {
        setMessages(prev => [...prev, { role: "system", text: data.note }]);
      }
    } catch (err) {
      console.error(err);
      alert("Network/upload error.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="chat-container p-4">
      <h1 className="text-2xl font-semibold mb-4">Artisan Interview Agent (ElevenLabs)</h1>

      <div className="mb-4 grid grid-cols-1 md:grid-cols-2 gap-2">
        <div>
          <label className="block text-sm text-gray-600">Agent ID</label>
          <input
            value={agentId}
            onChange={(e) => setAgentId(e.target.value)}
            className="w-full border rounded px-3 py-2"
            placeholder="Paste your agent id here" />
        </div>
        <div>
          <label className="block text-sm text-gray-600">Voice ID (optional)</label>
          <input
            value={voiceId}
            onChange={(e) => setVoiceId(e.target.value)}
            className="w-full border rounded px-3 py-2"
            placeholder="Paste voice id for TTS (optional)" />
        </div>
      </div>

      <div className="border rounded-lg p-4 h-80 overflow-auto mb-4 bg-white">
        {messages.length === 0 && <div className="text-gray-500">Say “Hello” or type below.</div>}
        {messages.map((m, i) => (
          <div key={i} className={`mb-3 ${m.role === "agent" ? "text-left" : m.role === "user" ? "text-right" : "text-center text-sm text-gray-400"}`}>
            <div className={`${m.role === "agent" ? "inline-block bg-gray-100 p-3 rounded-lg max-w-[80%]" : m.role === "user" ? "inline-block bg-blue-100 p-3 rounded-lg max-w-[80%]" : ""}`}>
              {m.text}
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-2 items-center mb-4">
        <button
          onMouseDown={startRecording}
          onMouseUp={stopRecording}
          onTouchStart={startRecording}
          onTouchEnd={stopRecording}
          className={`px-4 py-2 rounded ${recording ? "bg-red-500 text-white" : "bg-green-500 text-white"}`}>
          {recording ? "Recording… (release to stop)" : "Hold to Talk"}
        </button>

        <form onSubmit={sendText} className="flex gap-2 items-center flex-1">
          <input
            className="flex-1 border rounded px-3 py-2"
            placeholder="Type a message..."
            value={textInput}
            onChange={e => setTextInput(e.target.value)} />
          <button className="px-3 py-2 bg-blue-600 text-white rounded" type="submit" disabled={loading}>
            Send
          </button>
        </form>
      </div>

      <div className="mb-4 text-sm text-gray-600">
        <div>Last recorded blob size: {lastBlobRef.current ? `${lastBlobRef.current.size} bytes` : "none"}</div>
        <div>Tip: If blob size is 0, try another browser or switch to click-to-start/stop recording.</div>
      </div>

      <audio ref={audioRef} controls className="w-full" />
    </div>
  );
}
