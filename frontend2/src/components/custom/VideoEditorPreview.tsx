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
import { videoEditAPI } from "@/lib/api";
import type { TrendingSong, UserVideo } from "@/lib/api";

export default function VideoEditorPreview({ selectedVideoUrl = "/sample-video.mp4" }: { selectedVideoUrl?: string }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [progress, setProgress] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [prompt, setPrompt] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [showSongs, setShowSongs] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showMusicDialog, setShowMusicDialog] = useState(false);
  const [addedSongs, setAddedSongs] = useState<number[]>([]);
  
  // Track the current video URL (can be updated by edits)
  const [currentVideoUrl, setCurrentVideoUrl] = useState<string>(selectedVideoUrl);

  // New state for video editing integration
  const [trendingSongs, setTrendingSongs] = useState<TrendingSong[]>([]);
  const [editing, setEditing] = useState<boolean>(false);
  const [editType, setEditType] = useState<'prompt' | 'audio'>('prompt');
  const [selectedSongId, setSelectedSongId] = useState<number | null>(null);
  const [topic, setTopic] = useState<string>('kaarigar_project');
  const [saveName, setSaveName] = useState<string>('');

  // Load trending songs on component mount
  useEffect(() => {
    loadTrendingSongs();
  }, []);

  // Update currentVideoUrl when selectedVideoUrl prop changes
  useEffect(() => {
    setCurrentVideoUrl(selectedVideoUrl);
  }, [selectedVideoUrl]);

  // Update video source when currentVideoUrl changes
  useEffect(() => {
    if (currentVideoUrl && videoRef.current) {
      videoRef.current.src = currentVideoUrl;
    }
  }, [currentVideoUrl]);

  const loadTrendingSongs = async () => {
    try {
      const response = await videoEditAPI.getTrendingSongs();
      if (response.success) {
        setTrendingSongs(response.songs);
      }
    } catch (error) {
      console.error('Failed to load trending songs:', error);
    }
  };



  // AI Prompt Edit - matches test_req.py structure
  const handleEditVideo = async () => {
    if (!currentVideoUrl) return;
    
    setEditing(true);
    try {
      // AI Prompt Edit - exactly like test_req.py
      const response = await videoEditAPI.editVideo({
        video_url: currentVideoUrl,
        edit_prompt: prompt,
        topic: topic,
        save_name: saveName || `edited_${Date.now()}`
      });
      
      if (response.success) {
        // Update the current video URL with the edited video
        if (response.edited_video_url) {
          setCurrentVideoUrl(response.edited_video_url);
        }
        setShowEditDialog(false);
        setPrompt("");
        setTopic('kaarigar_project');
        setSaveName('');
        console.log('✅ Video edited successfully:', response);
      } else {
        console.error('❌ Edit failed:', response.error);
      }
    } catch (error) {
      console.error('❌ Edit error:', error);
    } finally {
      setEditing(false);
    }
  };

  // Separate function for adding trending audio
  const handleAddTrendingAudio = async () => {
    if (!currentVideoUrl || selectedSongId === null) return;
    
    setEditing(true);
    try {
      // Trending Audio - exactly like test_req_trending_audio.py
      const response = await videoEditAPI.addTrendingAudio({
        video_url: currentVideoUrl,
        song_id: selectedSongId,
        topic: topic,
        save_name: saveName || `trending_audio_${Date.now()}`
      });
      
      if (response.success) {
        // Update the current video URL with the edited video
        if (response.edited_video_url) {
          setCurrentVideoUrl(response.edited_video_url);
        }
        setShowMusicDialog(false);
        setSelectedSongId(null);
        setTopic('kaarigar_project');
        setSaveName('');
        console.log('✅ Trending audio added successfully:', response);
      } else {
        console.error('❌ Add audio failed:', response.error);
      }
    } catch (error) {
      console.error('❌ Add audio error:', error);
    } finally {
      setEditing(false);
    }
  };

  // Update the songs array to use real trending songs
  const songs = trendingSongs.map((song, index) => ({
    id: index,
    title: song.title,
    artist: song.artist,
    duration: song.duration
  }));

  // Video progress tracking
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
                    onClick={() => setShowMusicDialog(true)}
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
                    onClick={() => {
                      setShowEditDialog(true);
                    }}
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

      {/* Enhanced AI Edit Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="bg-white border-gray-700 max-h-[80vh] !max-w-[20vw] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Edit Video with AI
            </DialogTitle>
          </DialogHeader>
          
          {/* Selected Video Info */}
          <div className="mb-4 p-3 bg-blue-900/20 border border-blue-500 rounded-lg">
            <p className="text-sm text--300 font-medium">Editing Video:</p>
            <p className="text-sm text-">{currentVideoUrl.split('/').pop()}</p>
            <p className="text-xs text--400">Ready to edit with AI prompts</p>
          </div>

          {/* AI Prompt Edit - matches test_req.py */}
          <Card className="border border-gray-700 bg-gray-800">
            <CardContent className="p-4 flex flex-col gap-3 text-white">
                <div>
                  <label className="block text-sm font-medium mb-2">Edit Prompt</label>
              <Input
                    placeholder="e.g., make the video vertical, make it black and white, rotate 90 degrees..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                    className="bg-gray-700 border-gray-600 text-white"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">Topic</label>
                  <Input
                    placeholder="e.g., my_project, kaarigar_project"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    className="bg-gray-700 border-gray-600 text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Save Name (optional)</label>
                  <Input
                    placeholder="e.g., edited_video_123"
                    value={saveName}
                    onChange={(e) => setSaveName(e.target.value)}
                    className="bg-gray-700 border-gray-600 text-white"
                  />
                </div>
                
                <div className="text-xs text-gray-400">
                  <p className="font-medium mb-1">Example prompts from your tests:</p>
                  <ul className="list-disc list-inside space-y-1">
                    <li>"make the video vertical"</li>
                    <li>"make it black and white"</li>
                    <li>"rotate 90 degrees clockwise"</li>
                    <li>"add blur effect"</li>
                    <li>"make it portrait for Instagram"</li>
                  </ul>
                </div>
                
                <Button 
                  onClick={handleEditVideo}
                  disabled={!prompt.trim() || editing || !currentVideoUrl}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {editing ? 'Processing...' : 'Generate Edit'}
                </Button>
              </CardContent>
            </Card>
        </DialogContent>
      </Dialog>

      {/* Separate Music/Trending Audio Dialog */}
      <Dialog open={showMusicDialog} onOpenChange={setShowMusicDialog}>
        <DialogContent className="text-black border-gray-700 max-h-[80vh] !max-w-[20vw] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Add Trending Audio to Video
            </DialogTitle>
          </DialogHeader>
          
          {/* Selected Video Info */}
          <div className="mb-4 p-3 bg-blue-900/20 border border-blue-500 rounded-lg">
            <p className="text-sm text-300 font-medium">Adding Audio to:</p>
            <p className="text-sm text-">{currentVideoUrl.split('/').pop()}</p>
            <p className="text-xs text--400">Select a trending song to add to your video</p>
          </div>

          {/* Trending Songs Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2 text-black">Select Trending Song</label>
            
            {trendingSongs.length > 0 ? (
              <div className="grid grid-cols-1 gap-2 max-h-60 overflow-y-auto border border-gray-600 rounded-lg p-2">
                {trendingSongs.map((song, index) => (
                  <div
                    key={index}
                    onClick={() => setSelectedSongId(index)}
                    className={`p-3 border rounded-lg cursor-pointer transition-colors hover:bg-gray-700 hover:text-white ${
                      selectedSongId === index ? 'border-green-500 bg-green-900/30' : 'border-gray-600'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-">{song.title}</p>
                        <p className="text-xs text--400">{song.artist}</p>
                      </div>
                      <div className="text-xs text--500">
                        ID: {index}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-4 text-gray-400 border border-gray-600 rounded-lg">
                Loading trending songs...
              </div>
            )}
          </div>

          {/* Input Fields */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2 text-white">Topic</label>
              <Input
                placeholder="e.g., my_project, kaarigar_project"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                className="bg-gray-700 border-gray-600 text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2 text-white">Save Name (optional)</label>
              <Input
                placeholder="e.g., trending_audio_123"
                value={saveName}
                onChange={(e) => setSaveName(e.target.value)}
                className="bg-gray-700 border-gray-600 text-white"
              />
            </div>
          </div>
          
          {/* Add Audio Button */}
          <Button 
            onClick={handleAddTrendingAudio}
            disabled={selectedSongId === null || editing || !currentVideoUrl}
            className="bg-green-600 hover:bg-green-700 w-full mt-4"
          >
            {editing ? 'Adding Audio...' : 'Add Trending Audio to Video'}
          </Button>
        </DialogContent>
      </Dialog>
    </div>
  );
}
