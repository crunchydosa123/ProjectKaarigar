import { ClosedCaption } from "lucide-react";
import { useRef, useState, useEffect } from "react";
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function VideoEditorPreview() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [progress, setProgress] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [prompt, setPrompt] = useState("");

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const updateProgress = () => {
      const progressPercent = (video.currentTime / video.duration) * 100;
      setProgress(progressPercent);
      setCurrentTime(video.currentTime);
      setDuration(video.duration);
    };

    video.addEventListener("timeupdate", updateProgress);
    return () => video.removeEventListener("timeupdate", updateProgress);
  }, []);

  const formatTime = (t: number) => {
    if (isNaN(t)) return "00:00";
    const m = Math.floor(t / 60)
      .toString()
      .padStart(2, "0");
    const s = Math.floor(t % 60)
      .toString()
      .padStart(2, "0");
    return `${m}:${s}`;
  };

  return (
    <div className="bg-[#1e1e1e] text-white shadow-lg w-full max-w-3xl mx-auto rounded-lg border border-gray-700 p-4">
      {/* Video Preview */}
      <div className="relative bg-black overflow-hidden rounded-md">
        <video
          ref={videoRef}
          src="/sample-video.mp4"
          controls
          className="w-full h-80 object-cover"
        />
        <div className="absolute bottom-2 right-3 text-xs bg-black/60 px-2 py-1 rounded">
          {formatTime(currentTime)} / {formatTime(duration)}
        </div>
      </div>

      {/* Timeline */}
      <div className="mt-4 bg-gray-900 relative h-20 flex items-center overflow-hidden rounded-md border border-gray-800">
        {Array.from({ length: 12 }).map((_, i) => (
          <div
            key={i}
            className="absolute top-0 bottom-0 border-l border-gray-700"
            style={{ left: `${(i / 12) * 100}%` }}
          />
        ))}

        {/* Playhead */}
        <div
          className="absolute top-0 bottom-0 w-[2px] bg-red-500 transition-all duration-100 linear"
          style={{ left: `${progress}%` }}
        />

        {/* Timestamps */}
        <div className="absolute bottom-1 left-0 right-0 flex justify-between text-[10px] text-gray-400 px-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <span key={i}>{formatTime((i / 6) * duration)}</span>
          ))}
        </div>
      </div>

      {/* Controls below timeline */}
      <div className="mt-3 flex justify-between items-center">
        <Popover>
          <PopoverTrigger asChild>
            <Button>Edit with AI</Button>
          </PopoverTrigger>
          <PopoverContent>
            <Card className="border border-white">
              <CardTitle className="p-4 pb-0">Edit Video with AI</CardTitle>
              <CardContent className="p-4 flex flex-col gap-3">
                <Input
                  placeholder="Describe the edit you want..."
                  value={prompt}
                  onChange={(e: any) => setPrompt(e.target.value)}
                  className=""
                />
                <Button
                  onClick={() => console.log("AI prompt:", prompt)}
                >
                  Generate Edit
                </Button>
              </CardContent>
            </Card>
          </PopoverContent>
        </Popover>

        <Button
          variant="secondary"
          className="flex items-center gap-1 bg-gray-700 hover:bg-gray-600"
        >
          <ClosedCaption className="w-4 h-4" />
          Subtitles
        </Button>
      </div>
    </div>
  );
}
