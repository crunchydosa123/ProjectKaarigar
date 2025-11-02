import { useEffect, useRef, useState } from 'react';
import { usePage } from '@/contexts/PageContext';
import {
  House,
  Mic,
  MicOff,
  Captions,
  Camera,
  X,
  Upload,
  ArrowRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from '@/components/ui/popover';

const AICameraman = () => {
  const { setCurrentPage } = usePage();
  const videoRef = useRef<HTMLVideoElement>(null);
  const [muted, setMuted] = useState(false);
  const [photos, setPhotos] = useState<string[]>([]);

  useEffect(() => {
    navigator.mediaDevices
      .getUserMedia({ video: true, audio: true })
      .then((stream) => {
        if (videoRef.current) videoRef.current.srcObject = stream;
      })
      .catch((err) => console.error('Error accessing camera:', err));

    return () => {
      const stream = videoRef.current?.srcObject as MediaStream;
      stream?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  const toggleMute = () => {
    setMuted((prev) => !prev);
    const stream = videoRef.current?.srcObject as MediaStream;
    if (stream) {
      stream.getAudioTracks().forEach((track) => (track.enabled = muted));
    }
  };

  const capturePhoto = () => {
    const video = videoRef.current;
    if (!video) return;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 300;
    canvas.height = video.videoHeight || 350;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL('image/png');
      setPhotos((prev) => [dataUrl, ...prev]);
    }
  };

  const deletePhoto = (index: number) => {
    setPhotos((prev) => prev.filter((_, i) => i !== index));
  };

  const uploadPhotos = () => {
    // implement upload logic (to cloud, backend, etc.)
    console.log('Uploading photos:', photos);
    alert('Photos uploaded successfully!');
  };

  const goNext = () => {
    // Navigate or perform next step
    setCurrentPage('nextPage'); // example
  };

  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden relative"
      style={{ backgroundImage: "url('/white_bg.png')" }}
    >
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3">
        <button
          className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white"
          onClick={() => setCurrentPage('home')}
        >
          <House />
        </button>
        <div className="text-md font-bold ml-3">AI Cameraman</div>
      </div>

      {/* Camera Feed */}
      <div className="flex flex-col justify-center items-center mt-5">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted={muted}
          className="rounded-xl border shadow-md w-[300px] h-[350px] max-w-lg bg-black object-cover"
        ></video>
      </div>

      {/* Controls */}
      <div className="flex justify-center gap-4 mt-6">
        <Button
          variant="outline"
          className="h-12 w-12 flex items-center justify-center"
          onClick={toggleMute}
        >
          {muted ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
        </Button>

        <Button
          variant="default"
          className="h-12 w-12 flex items-center justify-center bg-blue-500 hover:bg-blue-600 text-white"
          onClick={capturePhoto}
        >
          <Camera className="h-5 w-5" />
        </Button>

        <Button
          variant="outline"
          className="h-12 w-12 flex items-center justify-center"
        >
          <Captions className="h-5 w-5" />
        </Button>
      </div>

      {/* Captured Photos Preview */}
      {photos.length > 0 && (
        <div className="mt-6 flex flex-col items-center">
          <div className="flex gap-2 overflow-x-auto w-full px-4">
            {photos.slice(0, 4).map((photo, i) => (
              <div key={i} className="relative">
                <img
                  src={photo}
                  alt={`capture-${i}`}
                  className="w-20 h-20 object-cover rounded-md border shadow"
                />
                <button
                  className="absolute top-0 right-0 bg-black/50 rounded-full p-1 hover:bg-black"
                  onClick={() => deletePhoto(i)}
                >
                  <X className="w-4 h-4 text-white" />
                </button>
              </div>
            ))}
          </div>

          {/* Popover for viewing all photos */}
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" className="mt-4">
                View All Captures
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[300px] max-h-[400px] overflow-y-auto p-2">
              <div className="grid grid-cols-2 gap-2">
                {photos.map((photo, i) => (
                  <div key={i} className="relative">
                    <img
                      src={photo}
                      alt={`full-${i}`}
                      className="w-full h-32 object-cover rounded-md border"
                    />
                    <button
                      className="absolute top-1 right-1 bg-black/50 rounded-full p-1 hover:bg-black"
                      onClick={() => deletePhoto(i)}
                    >
                      <X className="w-4 h-4 text-white" />
                    </button>
                  </div>
                ))}
              </div>
            </PopoverContent>
          </Popover>

          {/* Upload & Next Buttons */}
          <div className="flex gap-4 mt-6">
            <Button
              onClick={goNext}
              variant="default"
              className="flex items-center gap-2 bg-purple-500 hover:bg-purple-600 text-white"
            >
              Upload  and Next <ArrowRight className="h-5 w-5" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AICameraman;
