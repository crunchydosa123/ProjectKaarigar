import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Conversational from "./pages/Conversational";
import VideoEditor from "./pages/VideoEditor";

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
