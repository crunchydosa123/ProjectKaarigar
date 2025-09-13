import React from "react";
import { Upload, Mic, MicOff, Send } from "lucide-react";

export default function EditorControls({
  conversationState,
  recognitionRef,
  listening,
  setListening,
  uploading,
  inputText,
  setInputText,
  startListening,
  handleFileChange,
  handleTextSubmit
}) {
  return (
    <div>
      {conversationState === "upload_video" && (
        <div className="relative">
          <input
            type="file"
            accept="video/*"
            onChange={handleFileChange}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            id="video-upload"
          />
          <label
            htmlFor="video-upload"
            className="flex items-center justify-center w-full py-4 px-6 border-2 border-dashed border-purple-200 rounded-2xl bg-gradient-to-r from-purple-50 to-pink-50 hover:from-purple-100 hover:to-pink-100 transition-all duration-300 cursor-pointer group"
          >
            <Upload className="w-6 h-6 text-purple-600 mr-3 group-hover:scale-110 transition-transform" />
            <span className="text-purple-600 font-medium">Choose Video File</span>
          </label>
        </div>
      )}

      {(conversationState === "get_prompt" || conversationState === "review") && (
        <div className="space-y-3">
          <button
            onClick={() => {
              if (recognitionRef.current && !listening) {
                setListening(true);
                recognitionRef.current.start();
              } else {
                startListening();
              }
            }}

            className={`w-full py-4 px-6 rounded-2xl font-medium transition-all duration-300 flex items-center justify-center shadow-lg ${listening
                ? "bg-gradient-to-r from-purple-300 to-pink-300 text-white animate-pulse"
                : uploading
                  ? "bg-purple-200 text-purple-400 cursor-not-allowed"
                  : "bg-gradient-to-r from-purple-300 to-purple-500 text-white hover:from-purple-350 hover:to-pink-300 transform hover:scale-[1.02] active:scale-[0.98]"
              }`}
          >
            {listening ? (
              <>
                <MicOff className="w-5 h-5 mr-2" />
                Listening...
              </>
            ) : uploading ? (
              <>
                <div className="w-5 h-5 mr-2 border-2 border-purple-300 border-t-transparent rounded-full animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Mic className="w-5 h-5 mr-2" />
                Voice Input
              </>
            )}
          </button>

          <div className="flex space-x-2">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && handleTextSubmit()}
              className="flex-1 px-4 py-3 border border-purple-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-pink-200 focus:border-transparent transition-all duration-200 bg-white/90"
              placeholder="Type your instructions..."
              disabled={uploading}
            />
            <button
              onClick={handleTextSubmit}
              disabled={uploading || !inputText.trim()}
              className={`px-6 py-3 rounded-xl font-medium transition-all duration-300 ${uploading || !inputText.trim()
                  ? "bg-purple-200 text-purple-400 cursor-not-allowed"
                  : "bg-gradient-to-r from-purple-300 to-pink-300 text-white hover:from-purple-400 hover:to-pink-400 shadow-lg transform hover:scale-105 active:scale-95"
                }`}
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
