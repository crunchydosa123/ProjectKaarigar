import React, { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Checkbox } from '../components/ui/checkbox';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { 
  Video, 
  Image, 
  Play, 
  Loader2, 
  CheckCircle, 
  XCircle, 
  ArrowLeft,
  Clock,
  FileVideo,
  ImageIcon
} from 'lucide-react';
// Define interfaces locally to avoid import issues
interface UserImage {
  id: string;
  public_url: string;
  title: string;
  filename: string;
  original_filename: string;
  uploaded_at: string;
}

interface GeneratedVideo {
  id: string;
  user_id: string;
  kaarigar_id: string;
  video_type: string;
  title: string;
  description: string;
  prompt: string;
  optimized_prompt: string;
  selected_images: UserImage[];
  duration_seconds: number;
  blob_path: string;
  public_url: string;
  file_size: number;
  generated_at: string;
  is_active: boolean;
}

// Define API interfaces locally
interface UserImagesResponse {
  success: boolean;
  images: UserImage[];
  count: number;
  error?: string;
}

interface GenerateVideoRequest {
  selected_image_ids: string[];
  prompt: string;
  title: string;
  description?: string;
  duration_seconds?: number;
}

interface GenerateVideoResponse {
  success: boolean;
  message: string;
  video_id?: string;
  public_url?: string;
  title?: string;
  error?: string;
}

interface GeneratedVideosResponse {
  success: boolean;
  videos: GeneratedVideo[];
  count: number;
  error?: string;
}

// Simple video API implementation
class VideoAPI {
  private baseURL: string = 'https://backend-557742533869.asia-south1.run.app/api/video';

  private async request<T>(
    endpoint: string,
    method: string = 'GET',
    data?: any
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    };

    if (data) {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, options);
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      return result;
    } catch (error) {
      console.error('Video API Error:', error);
      throw error;
    }
  }

  async getUserImages(): Promise<UserImagesResponse> {
    return this.request<UserImagesResponse>('/get-user-images', 'GET');
  }

  async generateVideo(request: GenerateVideoRequest): Promise<GenerateVideoResponse> {
    return this.request<GenerateVideoResponse>('/generate-video', 'POST', request);
  }

  async getGeneratedVideos(): Promise<GeneratedVideosResponse> {
    return this.request<GeneratedVideosResponse>('/get-generated-videos', 'GET');
  }

  async healthCheck(): Promise<{ status: string; service: string; firestore_available: boolean; storage_available: boolean; genai_available: boolean; ffmpeg_available: boolean }> {
    return this.request('/health', 'GET');
  }
}

const videoAPI = new VideoAPI();

interface GenerateVideoProps {
  onBack: () => void;
}

const GenerateVideo: React.FC<GenerateVideoProps> = ({ onBack }) => {
  const [userImages, setUserImages] = useState<UserImage[]>([]);
  const [selectedImageIds, setSelectedImageIds] = useState<string[]>([]);
  const [prompt, setPrompt] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [durationSeconds, setDurationSeconds] = useState(4);
  const [generating, setGenerating] = useState(false);
  const [generationStatus, setGenerationStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [generationMessage, setGenerationMessage] = useState('');
  const [generatedVideos, setGeneratedVideos] = useState<GeneratedVideo[]>([]);
  const [loadingImages, setLoadingImages] = useState(true);
  const [loadingVideos, setLoadingVideos] = useState(true);
  const [isImageModalOpen, setIsImageModalOpen] = useState(false);
  const [isHelpModalOpen, setIsHelpModalOpen] = useState(false);

  // Load user images on component mount
  useEffect(() => {
    loadUserImages();
    loadGeneratedVideos();
  }, []);

  const loadUserImages = async () => {
    try {
      setLoadingImages(true);
      const response = await videoAPI.getUserImages();
      if (response.success) {
        setUserImages(response.images);
        console.log(`📁 Loaded ${response.images.length} user images`);
      } else {
        console.error('Failed to load user images:', response.error);
      }
    } catch (error) {
      console.error('Error loading user images:', error);
    } finally {
      setLoadingImages(false);
    }
  };

  const loadGeneratedVideos = async () => {
    try {
      setLoadingVideos(true);
      const response = await videoAPI.getGeneratedVideos();
      if (response.success) {
        setGeneratedVideos(response.videos);
        console.log(`🎬 Loaded ${response.videos.length} generated videos`);
      } else {
        console.error('Failed to load generated videos:', response.error);
      }
    } catch (error) {
      console.error('Error loading generated videos:', error);
    } finally {
      setLoadingVideos(false);
    }
  };

  const handleImageSelect = (imageId: string) => {
    setSelectedImageIds(prev => 
      prev.includes(imageId) 
        ? prev.filter(id => id !== imageId)
        : [...prev, imageId]
    );
  };

  const handleSelectAll = () => {
    if (selectedImageIds.length === userImages.length) {
      setSelectedImageIds([]);
    } else {
      setSelectedImageIds(userImages.map(img => img.id));
    }
  };

  const handleGenerateVideo = async () => {
    if (selectedImageIds.length === 0) {
      setGenerationStatus('error');
      setGenerationMessage('Please select at least one image');
      return;
    }

    if (!prompt.trim()) {
      setGenerationStatus('error');
      setGenerationMessage('Please enter a prompt');
      return;
    }

    if (!title.trim()) {
      setGenerationStatus('error');
      setGenerationMessage('Please enter a title');
      return;
    }

    try {
      setGenerating(true);
      setGenerationStatus('idle');
      setGenerationMessage('');

      console.log('🎬 Starting video generation...');
      console.log('Selected images:', selectedImageIds);
      console.log('Prompt:', prompt);
      console.log('Title:', title);

      const response = await videoAPI.generateVideo({
        selected_image_ids: selectedImageIds,
        prompt: prompt.trim(),
        title: title.trim(),
        description: description.trim(),
        duration_seconds: durationSeconds
      });

      if (response.success) {
        setGenerationStatus('success');
        setGenerationMessage(`Video "${response.title}" generated successfully!`);
        console.log('✅ Video generated successfully:', response);
        
        // Refresh the generated videos list
        loadGeneratedVideos();
        
        // Reset form
        setSelectedImageIds([]);
        setPrompt('');
        setTitle('');
        setDescription('');
      } else {
        setGenerationStatus('error');
        setGenerationMessage(response.error || 'Video generation failed');
        console.error('❌ Video generation failed:', response.error);
      }
    } catch (error) {
      setGenerationStatus('error');
      setGenerationMessage(error instanceof Error ? error.message : 'Video generation failed');
      console.error('❌ Video generation error:', error);
    } finally {
      setGenerating(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 p-4">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <Button
            onClick={onBack}
            variant="outline"
            size="sm"
            className="flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </Button>
          <div className="flex items-center gap-2">
            <Video className="w-6 h-6 text-purple-600" />
            <h1 className="text-2xl font-bold text-gray-900">Generate Video</h1>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column - Video Generation Form */}
          <div className="space-y-6">
            {/* Generation Form */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Play className="w-5 h-5 text-purple-600" />
                  Create New Video
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Title Input */}
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-2 block">
                    Video Title *
                  </label>
                  <Input
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Enter video title"
                    disabled={generating}
                  />
                </div>

                {/* Description Input */}
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-2 block">
                    Description
                  </label>
                  <Textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Enter video description (optional)"
                    rows={3}
                    disabled={generating}
                  />
                </div>

                {/* Prompt Input */}
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-2 block">
                    Video Prompt *
                  </label>
                  <Textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="Describe the video style, camera movements, effects, etc."
                    rows={3}
                    disabled={generating}
                  />
                </div>

                {/* Duration Input */}
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-2 block">
                    Duration per Image (seconds)
                  </label>
                  <Input
                    type="number"
                    value={durationSeconds}
                    onChange={(e) => setDurationSeconds(parseInt(e.target.value) || 4)}
                    min="1"
                    max="10"
                    disabled={generating}
                  />
                </div>

                {/* Generate Button */}
                <Button
                  onClick={handleGenerateVideo}
                  disabled={generating || selectedImageIds.length === 0 || !prompt.trim() || !title.trim()}
                  className="w-full bg-purple-600 hover:bg-purple-700 text-white"
                >
                  {generating ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Generating Video...
                    </>
                  ) : (
                    <>
                      <Video className="w-4 h-4 mr-2" />
                      Generate Video
                    </>
                  )}
                </Button>

                {/* Status Message */}
                {generationMessage && (
                  <div className={`p-3 rounded-md flex items-center gap-2 ${
                    generationStatus === 'success' 
                      ? 'bg-green-50 text-green-800 border border-green-200' 
                      : 'bg-red-50 text-red-800 border border-red-200'
                  }`}>
                    {generationStatus === 'success' ? (
                      <CheckCircle className="w-4 h-4" />
                    ) : (
                      <XCircle className="w-4 h-4" />
                    )}
                    {generationMessage}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Image Selection */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Image className="w-5 h-5 text-purple-600" />
                    Selected Images ({selectedImageIds.length})
                  </div>
                  <div className="flex gap-2">
                    <Button
                      onClick={() => setIsImageModalOpen(true)}
                      variant="outline"
                      size="sm"
                    >
                      <Image className="w-4 h-4 mr-1" />
                      Choose Images
                    </Button>
                    <Button
                      onClick={() => setIsHelpModalOpen(true)}
                      variant="outline"
                      size="sm"
                    >
                      <Video className="w-4 h-4 mr-1" />
                      Help
                    </Button>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {selectedImageIds.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <ImageIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                    <p>No images selected. Click "Choose Images" to select images for your video.</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <p className="text-sm text-gray-600 mb-3">
                      {selectedImageIds.length} image{selectedImageIds.length !== 1 ? 's' : ''} selected
                    </p>
                    <div className="grid grid-cols-3 gap-2 max-h-32 overflow-y-auto">
                      {selectedImageIds.map((imageId) => {
                        const image = userImages.find(img => img.id === imageId);
                        return image ? (
                          <div key={imageId} className="relative">
                            <img
                              src={image.public_url}
                              alt={image.title || image.filename}
                              className="w-full h-16 object-cover rounded border"
                            />
                            <button
                              onClick={() => handleImageSelect(imageId)}
                              className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs hover:bg-red-600"
                            >
                              ×
                            </button>
                          </div>
                        ) : null;
                      })}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Generated Videos */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileVideo className="w-5 h-5 text-purple-600" />
                  Generated Videos
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loadingVideos ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
                    <span className="ml-2 text-gray-600">Loading videos...</span>
                  </div>
                ) : generatedVideos.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <FileVideo className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                    <p>No videos generated yet. Create your first video!</p>
                  </div>
                ) : (
                  <div className="space-y-4 max-h-96 overflow-y-auto">
                    {generatedVideos.map((video) => (
                      <div
                        key={video.id}
                        className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="font-medium text-gray-900 truncate">
                            {video.title}
                          </h3>
                          <Badge variant="secondary" className="text-xs">
                            {video.duration_seconds}s per image
                          </Badge>
                        </div>
                        
                        <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                          {video.description || video.prompt}
                        </p>
                        
                        <div className="flex items-center justify-between text-xs text-gray-500">
                          <div className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {formatDate(video.generated_at)}
                          </div>
                          <div className="flex items-center gap-1">
                            <Image className="w-3 h-3" />
                            {video.selected_images.length} images
                          </div>
                        </div>
                        
                        <div className="mt-3">
                          <Button
                            onClick={() => window.open(video.public_url, '_blank')}
                            size="sm"
                            className="w-full"
                          >
                            <Play className="w-3 h-3 mr-1" />
                            View Video
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Image Selection Modal */}
        <Dialog open={isImageModalOpen} onOpenChange={setIsImageModalOpen}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Image className="w-5 h-5 text-purple-600" />
                Choose Images for Video Generation
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              {loadingImages ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
                  <span className="ml-2 text-gray-600">Loading images...</span>
                </div>
              ) : userImages.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <ImageIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>No images found. Upload some images first to generate videos.</p>
                </div>
              ) : (
                <>
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-gray-600">
                      Select images to include in your video ({selectedImageIds.length} selected)
                    </p>
                    <div className="flex gap-2">
                      <Button
                        onClick={handleSelectAll}
                        variant="outline"
                        size="sm"
                      >
                        {selectedImageIds.length === userImages.length ? 'Deselect All' : 'Select All'}
                      </Button>
                    </div>
                  </div>
                  <div className="grid grid-cols-4 gap-4 max-h-96 overflow-y-auto">
                    {userImages.map((image) => (
                      <div
                        key={image.id}
                        className={`relative border-2 rounded-lg overflow-hidden cursor-pointer transition-all ${
                          selectedImageIds.includes(image.id)
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-gray-200 hover:border-purple-300'
                        }`}
                        onClick={() => handleImageSelect(image.id)}
                      >
                        <img
                          src={image.public_url}
                          alt={image.title || image.filename}
                          className="w-full h-32 object-cover"
                        />
                        <div className="absolute top-2 left-2">
                          <Checkbox
                            checked={selectedImageIds.includes(image.id)}
                            onChange={() => handleImageSelect(image.id)}
                            className="bg-white/80"
                          />
                        </div>
                        <div className="p-2">
                          <p className="text-xs font-medium text-gray-900 truncate">
                            {image.title || image.original_filename}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          </DialogContent>
        </Dialog>

        {/* Help Modal */}
        <Dialog open={isHelpModalOpen} onOpenChange={setIsHelpModalOpen}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Video className="w-5 h-5 text-purple-600" />
                Video Generation Help
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">How to Generate Videos</h3>
                <ol className="list-decimal list-inside space-y-2 text-sm text-gray-600">
                  <li>Upload images using the "Upload" button on the home page</li>
                  <li>Click "Choose Images" to select which images to use for video generation</li>
                  <li>Enter a descriptive prompt about the video style, camera movements, and effects</li>
                  <li>Set the duration for each image (1-10 seconds)</li>
                  <li>Click "Generate Video" to create your AI-powered video</li>
                </ol>
              </div>
              
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Prompt Tips</h3>
                <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                  <li>Be specific about camera movements: "zoom in", "pan left", "dolly forward"</li>
                  <li>Describe the mood: "cinematic", "dramatic", "peaceful", "energetic"</li>
                  <li>Mention lighting: "golden hour", "studio lighting", "natural light"</li>
                  <li>Add effects: "slow motion", "speed ramp", "fade transition"</li>
                  <li>Example: "Cinematic slow zoom with golden hour lighting and smooth transitions"</li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Best Practices</h3>
                <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                  <li>Select 3-8 images for best results</li>
                  <li>Choose high-quality, clear images</li>
                  <li>Use images with similar themes or subjects</li>
                  <li>Keep prompts concise but descriptive</li>
                  <li>Experiment with different durations for variety</li>
                </ul>
              </div>

              <div className="bg-blue-50 p-3 rounded-md">
                <p className="text-sm text-blue-800">
                  <strong>Note:</strong> Video generation may take several minutes depending on the number of images and complexity of the prompt. Please be patient during the process.
                </p>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default GenerateVideo;
