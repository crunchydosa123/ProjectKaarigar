import React, { useRef, useEffect } from "react";

export default function ChatWindow({ messages = [] }) {
  const scroller = useRef(null);

  useEffect(() => {
    if (scroller.current) scroller.current.scrollTop = scroller.current.scrollHeight;
  }, [messages]);

  return (
    <div ref={scroller} className="h-80 overflow-y-auto p-6 space-y-4">
      {messages.length === 0 ? (
        <div className="text-center text-gray-500 py-8">
          <div className="text-4xl mb-2">💬</div>
          <div>No messages yet</div>
          <div className="text-sm">Use voice or type to talk to the assistant</div>
        </div>
      ) : (
        messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-xs lg:max-w-sm px-4 py-3 rounded-2xl ${msg.role === "ai"
              ? "bg-gradient-to-r from-purple-50 to-purple-100 text-purple-800 border border-purple-200"
              : "bg-gradient-to-r from-purple-400 to-purple-500 text-white shadow-md"
              }`}>
              <p className="text-sm">{msg.content}</p>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
