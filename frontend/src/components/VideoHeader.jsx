import React from "react";
import { Video } from "lucide-react";

export default function VideoHeader() {
  return (
    <div className="text-center mb-6">
      <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl mb-4 shadow-lg">
        <Video className="w-8 h-8 text-white" />
      </div>
      <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-700 to-pink-600 bg-clip-text text-transparent">
        AI Video Editor
      </h1>
      <p className="text-purple-700 mt-2 font-medium">Professional video editing for artisans</p>
    </div>
  );
}
