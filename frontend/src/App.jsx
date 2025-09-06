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


export default function App() {
  return (
    <BrowserRouter>
      <div>
          <Routes>
            <Route path="/" element={<Conversational />} />
            <Route path="/editor" element={<VideoEditor />} />
            <Route path="*" element={<div className="p-8 bg-white rounded-lg shadow">Page not found</div>} />
          </Routes>
      </div>
    </BrowserRouter>
  );
}
