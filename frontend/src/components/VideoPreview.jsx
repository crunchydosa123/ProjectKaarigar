import React from "react";
import { History, Video } from "lucide-react";

export default function VideoPreview({ current, promptHistory = [] }) {
  return (
    <div className="bg-white/80 backdrop-blur-md rounded-xl shadow-2xl border border-purple-200 overflow-hidden">
      <div className="bg-gradient-to-r from-purple-200 to-pink-200 p-6">
        <h2 className="text-xl font-semibold flex items-center text-purple-700">
          <Video className="w-6 h-6 mr-3" />
          Video Preview
        </h2>
      </div>

      <div className="p-6">
        {current ? (
          <div className="space-y-4">
            <div className="relative rounded-2xl overflow-hidden shadow-2xl bg-purple-100">
              <video controls src={current.url} key={current.url} className="w-full h-auto" style={{ maxHeight: "400px" }} />
            </div>

            {promptHistory.length > 0 && (
              <div className="bg-purple-100 rounded-2xl p-4 border border-purple-200">
                <div className="flex items-center mb-3">
                  <History className="w-5 h-5 text-purple-600 mr-2" />
                  <span className="font-medium text-purple-700">Edit History</span>
                </div>
                <div className="space-y-2">
                  {promptHistory.map((prompt, idx) => (
                    <div key={idx} className="flex items-start">
                      <div className="w-6 h-6 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mr-3 mt-0.5 flex-shrink-0">
                        <span className="text-white text-xs font-bold">{idx + 1}</span>
                      </div>
                      <p className="text-sm text-purple-700 leading-relaxed">{prompt}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-80 text-purple-500">
            <div className="w-24 h-24 bg-purple-100 rounded-full flex items-center justify-center mb-4">
              <Video className="w-12 h-12 text-purple-700" />
            </div>
            <p className="text-lg font-medium text-purple-700">No video uploaded</p>
            <p className="text-sm text-center mt-2 text-purple-700">Upload a video file to start editing</p>
          </div>
        )}
      </div>
    </div>
  );
}
