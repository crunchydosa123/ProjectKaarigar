import {Music, Pencil, Play, Plus, Sparkles } from "lucide-react";
import { useRef, useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function VideoEditorPreview() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [progress, setProgress] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [prompt, setPrompt] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [showSongs, setShowSongs] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [addedSongs, setAddedSongs] = useState<number[]>([]);

  const songs = [
    { id: 1, title: "Dreamy Lo-Fi", artist: "DJ Chill" },
    { id: 2, title: "Cinematic Rise", artist: "Epic Tunes" },
    { id: 3, title: "Soft Piano", artist: "Relaxify" },
  ];

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
    <div className="relative bg-[#1e1e1e] text-white shadow-lg w-full max-w-3xl mx-auto rounded-lg border-gray-700 overflow-hidden">
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

        {/* Song List Panel */}
        <AnimatePresence>
          {showSongs && (
            <motion.div
              initial={{ opacity: 0, x: -100 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -100 }}
              transition={{ duration: 0.3 }}
              className="absolute top-1/2 left-20 -translate-y-1/2 bg-gray-900/90 p-4 rounded-lg w-64 border border-gray-700"
            >
              <h3 className="font-semibold mb-2">Add Background Music</h3>
              <div className="flex flex-col gap-2">
                {songs.map((song) => {

                  const isAdded = addedSongs.includes(song.id);

                  return (
                    <div
                      key={song.id}
                      className={`flex justify-between items-center text-sm p-2 rounded-md transition-colors ${isAdded ? "bg-green-800/70 border border-green-500" : "bg-gray-800"
                        }`}
                    >
                      <div>
                        <p className="font-medium">{song.title}</p>
                        <p className="text-gray-400">{song.artist}</p>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => console.log("Play:", song.title)}
                        >
                          <Play className="w-4 h-4" />
                        </Button>

                        {isAdded ? (
                          <Button
                            size="icon"
                            variant="ghost"
                            className="text-green-400"
                            onClick={() =>
                              setAddedSongs((prev) => prev.filter((id) => id !== song.id))
                            }
                          >
                            ✅
                          </Button>
                        ) : (
                          <Button
                            size="icon"
                            variant="ghost"
                            onClick={() =>
                              setAddedSongs((prev) => [...prev, song.id])
                            }
                          >
                            <Plus className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                  );
                })}

              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Floating Expandable Pencil Menu (Left Side) */}
        <div className="absolute bottom-25 left-5">
          <div className="relative flex flex-col items-center">
            <AnimatePresence>
              {menuOpen && (
                <>
                  {/* Song Icon */}
                  <motion.button
                    initial={{ opacity: 0, y: 0 }}
                    animate={{ opacity: 1, y: -60 }}
                    exit={{ opacity: 0, y: 0 }}
                    transition={{ duration: 0.3 }}
                    className="absolute w-12 h-12 rounded-full bg-blue-600 hover:bg-blue-500 flex items-center justify-center shadow-lg"
                    onClick={() => setShowSongs((prev) => !prev)}
                  >
                    <Music className="w-5 h-5 text-white" />
                  </motion.button>

                  {/* Edit (Sparkles) Icon */}
                  <motion.button
                    initial={{ opacity: 0, y: 0 }}
                    animate={{ opacity: 1, y: -120 }}
                    exit={{ opacity: 0, y: 0 }}
                    transition={{ duration: 0.3, delay: 0.05 }}
                    className="absolute w-12 h-12 rounded-full bg-purple-600 hover:bg-purple-500 flex items-center justify-center shadow-lg"
                    onClick={() => setShowEditDialog(true)}
                  >
                    <Sparkles className="w-5 h-5 text-white" />
                  </motion.button>
                </>
              )}
            </AnimatePresence>

            {/* Main Pencil Button */}
            <motion.button
              whileTap={{ scale: 0.9 }}
              className="w-14 h-14 rounded-full bg-blue-700 hover:bg-blue-600 flex items-center justify-center shadow-lg"
              onClick={() => setMenuOpen((prev) => !prev)}
            >
              <Pencil className="w-6 h-6 text-white" />
            </motion.button>
          </div>
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

        <div
          className="absolute top-0 bottom-0 w-[2px] bg-red-500 transition-all duration-100 linear"
          style={{ left: `${progress}%` }}
        />

        <div className="absolute bottom-1 left-0 right-0 flex justify-between text-[10px] text-gray-400 px-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <span key={i}>{formatTime((i / 6) * duration)}</span>
          ))}
        </div>
      </div>

      {/* AI Edit Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="bg-gray-900 border-gray-700">
          <DialogHeader>
            <DialogTitle>Edit Video with AI</DialogTitle>
          </DialogHeader>
          <Card className="border border-gray-700 bg-gray-800">
            <CardContent className="p-4 flex flex-col gap-3 text-white">
              <Input
                placeholder="Describe the edit you want..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
              />
              <Button onClick={() => console.log("AI prompt:", prompt)}>
                Generate Edit
              </Button>
            </CardContent>
          </Card>
        </DialogContent>
      </Dialog>
    </div>
  );
}
