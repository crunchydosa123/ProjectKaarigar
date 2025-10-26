import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
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
  ImageIcon,
  Sparkles
} from 'lucide-react';
import { mediaAPI, reelAPI, type MediaItem, type ReelGenerationRequest, type GeneratedReel } from '@/lib/api';

interface ReelMakerProps {
  onBack: () => void;
  onComplete?: () => void;
}

const ReelMaker: React.FC<ReelMakerProps> = ({ onBack, onComplete }) => {
  const [userImages, setUserImages] = useState<MediaItem[]>([]);
  const [selectedImageIds, setSelectedImageIds] = useState<string[]>([]);
  const [prompt, setPrompt] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [durationSeconds, setDurationSeconds] = useState(4);
  const [generating, setGenerating] = useState(false);
  const [generationStatus, setGenerationStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [generationMessage, setGenerationMessage] = useState('');
  const [generatedReels, setGeneratedReels] = useState<GeneratedReel[]>([]);
  const [loadingImages, setLoadingImages] = useState(true);
  const [loadingReels, setLoadingReels] = useState(true);
  const [isImageModalOpen, setIsImageModalOpen] = useState(false);

  // Load user images and generated reels on component mount
  useEffect(() => {
    loadUserImages();
    loadGeneratedReels();
  }, []);

  const loadUserImages = async () => {
    try {
      setLoadingImages(true);
      const response = await mediaAPI.listMediaByType('images');
      if (response.success) {
        setUserImages(response.media);
        console.log(`📁 Loaded ${response.media.length} user images`);
      } else {
        console.error('Failed to load user images:', response.error);
      }
    } catch (error) {
      console.error('Error loading user images:', error);
    } finally {
      setLoadingImages(false);
    }
  };

  const loadGeneratedReels = async () => {
    try {
      setLoadingReels(true);
      const response = await reelAPI.getGeneratedReels();
      if (response.success) {
        setGeneratedReels(response.reels);
        console.log(`🎬 Loaded ${response.reels.length} generated reels`);
      } else {
        console.error('Failed to load generated reels:', response.error);
      }
    } catch (error) {
      console.error('Error loading generated reels:', error);
    } finally {
      setLoadingReels(false);
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

  const handleGenerateReel = async () => {
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

      console.log('🎬 Starting reel generation...');
      console.log('Selected images:', selectedImageIds);
      console.log('Prompt:', prompt);
      console.log('Title:', title);

      const response = await reelAPI.generateReel({
        selected_image_ids: selectedImageIds,
        prompt: prompt.trim(),
        title: title.trim(),
        description: description.trim(),
        duration_seconds: durationSeconds
      });

      if (response.success) {
        setGenerationStatus('success');
        setGenerationMessage(`Reel "${response.title}" generated successfully!`);
        console.log('✅ Reel generated successfully:', response);
        
        // Refresh the generated reels list
        loadGeneratedReels();
        
        // Reset form
        setSelectedImageIds([]);
        setPrompt('');
        setTitle('');
        setDescription('');
        
        // Call onComplete if provided
        if (onComplete) {
          setTimeout(() => {
            onComplete();
          }, 2000);
        }
      } else {
        setGenerationStatus('error');
        setGenerationMessage(response.error || 'Reel generation failed');
        console.error('❌ Reel generation failed:', response.error);
      }
    } catch (error) {
      setGenerationStatus('error');
      setGenerationMessage(error instanceof Error ? error.message : 'Reel generation failed');
      console.error('❌ Reel generation error:', error);
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
    <div className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
         style={{ backgroundImage: "url('/white_bg.png')" }}>
      
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3">
        <button
          className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white"
          onClick={onBack}
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="text-md font-bold ml-3">Create Reel from Images</div>
      </div>

      <div className="px-4 py-4 space-y-4">
        {/* Generation Form */}
        <Card className="p-4">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-600" />
              Generate New Reel
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Title Input */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                Reel Title *
              </label>
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter reel title"
                disabled={generating}
                className="w-full"
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
                placeholder="Enter reel description (optional)"
                rows={2}
                disabled={generating}
                className="w-full"
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
                className="w-full"
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
                className="w-full"
              />
            </div>

            {/* Generate Button */}
            <Button
              onClick={handleGenerateReel}
              disabled={generating || selectedImageIds.length === 0 || !prompt.trim() || !title.trim()}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white"
            >
              {generating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Generating Reel...
                </>
              ) : (
                <>
                  <Video className="w-4 h-4 mr-2" />
                  Generate Reel
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
        <Card className="p-4">
          <CardHeader>
            <CardTitle className="text-lg flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Image className="w-5 h-5 text-purple-600" />
                Selected Images ({selectedImageIds.length})
              </div>
              <Button
                onClick={() => setIsImageModalOpen(true)}
                variant="outline"
                size="sm"
              >
                <Image className="w-4 h-4 mr-1" />
                Choose Images
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {selectedImageIds.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <ImageIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No images selected. Click "Choose Images" to select images for your reel.</p>
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

        {/* Generated Reels */}
        {generatedReels.length > 0 && (
          <Card className="p-4">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <FileVideo className="w-5 h-5 text-purple-600" />
                Generated Reels
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {generatedReels.map((reel) => (
                  <div
                    key={reel.id}
                    className="border border-gray-200 rounded-lg p-3 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-medium text-gray-900 truncate">
                        {reel.title}
                      </h3>
                      <Badge variant="secondary" className="text-xs">
                        {reel.duration_seconds}s per image
                      </Badge>
                    </div>
                    
                    <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                      {reel.description || reel.prompt}
                    </p>
                    
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatDate(reel.generated_at)}
                      </div>
                      <div className="flex items-center gap-1">
                        <Image className="w-3 h-3" />
                        {reel.selected_image_ids.length} images
                      </div>
                    </div>
                    
                    <div className="mt-3">
                      <Button
                        onClick={() => window.open(reel.public_url, '_blank')}
                        size="sm"
                        className="w-full"
                      >
                        <Play className="w-3 h-3 mr-1" />
                        View Reel
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Image Selection Modal */}
      <Dialog open={isImageModalOpen} onOpenChange={setIsImageModalOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Image className="w-5 h-5 text-purple-600" />
              Choose Images for Reel Generation
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
                <p>No images found. Upload some images first to generate reels.</p>
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <p className="text-sm text-gray-600">
                    Select images to include in your reel ({selectedImageIds.length} selected)
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
    </div>
  );
};

export default ReelMaker;
