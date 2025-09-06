import React from "react";
import { BrowserRouter, Routes, Route, NavLink, Navigate } from "react-router-dom";
import Conversational from "./Conversational";
import VideoEditor from "./VideoEditor";
import './index.css';

/**
 * App.jsx - Router + top nav
 *
 * Expects:
 *  - src/ArtisanConversation.jsx  (default export: React component)
 *  - src/VideoEditor.jsx          (default export: React component)
 *
 * Styling uses Tailwind classes (already in your project).
 */

function TopNav() {
  const baseLink =
    "px-4 py-2 rounded-full text-sm font-medium transition-colors inline-flex items-center gap-2";
  const active = "bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg";
  const inactive = "bg-white text-gray-700 border border-gray-200 hover:shadow-sm";

  return (
    <div className="w-full bg-white/60 backdrop-blur-sm border-b border-gray-100">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-r from-purple-500 to-indigo-600 flex items-center justify-center text-white font-bold shadow-md">
            AI
          </div>
          <div>
            <div className="text-lg font-semibold">Artisan Studio</div>
            <div className="text-xs text-gray-500">Audio-first interviews & video editing</div>
          </div>
        </div>

        <nav className="flex items-center gap-3">
          <NavLink
            to="/artisan"
            className={({ isActive }) => `${baseLink} ${isActive ? active : inactive}`}
          >
            Artisan Conversation
          </NavLink>

          <NavLink
            to="/editor"
            className={({ isActive }) => `${baseLink} ${isActive ? active : inactive}`}
          >
            Video Editor
          </NavLink>
        </nav>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
        <TopNav />

        <main className="max-w-6xl mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Navigate to="/artisan" replace />} />
            <Route path="/artisan" element={<Conversational />} />
            <Route path="/editor" element={<VideoEditor />} />
            <Route path="*" element={<div className="p-8 bg-white rounded-lg shadow">Page not found</div>} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
