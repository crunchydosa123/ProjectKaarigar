import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  Play, 
  Loader2, 
  CheckCircle, 
  XCircle, 
  ArrowLeft,
  Clock,
  FileVideo,
  Sparkles,
  Image as ImageIcon,
  FileEdit,
  Trash2
} from 'lucide-react';
import { mediaAPI, reelGeneratorAPI, imageGenAPI, type GeneratedReel, type MediaItem } from '@/lib/api';
import { usePage } from '@/contexts/PageContext';
import { Input } from '@/components/ui/input';

interface ReelMakerProps {
  onBack: () => void;
  onComplete?: () => void;
}

interface CombinedImageItem extends MediaItem {
  type: 'uploaded' | 'edited';
}

const ReelMaker: React.FC<ReelMakerProps> = ({ onBack, onComplete }) => {
  const { user, setCurrentPage } = usePage();
  const [userImages, setUserImages] = useState<CombinedImageItem[]>([]);
  const [selectedImageIds, setSelectedImageIds] = useState<string[]>([]);
  const [prompt, setPrompt] = useState('');
  const [reelTitle, setReelTitle] = useState('');
  const [generating, setGenerating] = useState(false);
  const [generationStatus, setGenerationStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [generationMessage, setGenerationMessage] = useState('');
  const [generatedReels, setGeneratedReels] = useState<GeneratedReel[]>([]);
  const [loadingImages, setLoadingImages] = useState(true);
  const [isImageModalOpen, setIsImageModalOpen] = useState(false);
  const [resultVideoUrl, setResultVideoUrl] = useState<string | null>(null);
  const [allVideos, setAllVideos] = useState<any[]>([]);
  const [loadingAllVideos, setLoadingAllVideos] = useState(false);
  const [showAllVideos, setShowAllVideos] = useState(false);
  const [isVideosModalOpen, setIsVideosModalOpen] = useState(false);
  
  // AI Script Suggestion states
  const [suggestingScript, setSuggestingScript] = useState(false);
  const [scriptSuggestions, setScriptSuggestions] = useState<string[]>([]);
  const [selectedSuggestion, setSelectedSuggestion] = useState<string | null>(null);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Load user images and generated reels on component mount
  useEffect(() => {
    loadUserImages();
    loadGeneratedReels();
  }, []);

  const loadUserImages = async () => {
    try {
      console.log('🔄 Starting to load user images...');
      setLoadingImages(true);
      
      // Load both regular images and edited images
      const [imagesResponse, editedImagesResponse] = await Promise.all([
        mediaAPI.listMediaByType('images'),
        imageGenAPI.getGeneratedImages()
      ]);
      
      console.log('📡 Media API response (images):', imagesResponse);
      console.log('📡 Media API response (edited images):', editedImagesResponse);
      
      const allImages: CombinedImageItem[] = [];
      
      // Add regular images
      if (imagesResponse.success) {
        const regularImages: CombinedImageItem[] = imagesResponse.media.map((img: MediaItem) => ({
          ...img,
          type: 'uploaded' as const
        }));
        allImages.push(...regularImages);
        console.log(`📁 Loaded ${regularImages.length} regular images`);
      }
      
      // Add edited images
      if (editedImagesResponse.success) {
        const editedImages: CombinedImageItem[] = editedImagesResponse.images.map((img: any) => ({
          ...img,
          type: 'edited' as const
        }));
        allImages.push(...editedImages);
        console.log(`🎨 Loaded ${editedImages.length} edited images`);
      }
      
      setUserImages(allImages);
      console.log(`📁 Successfully loaded ${allImages.length} total images (${allImages.filter(img => img.type === 'uploaded').length} uploaded + ${allImages.filter(img => img.type === 'edited').length} edited):`, allImages);
      
    } catch (error) {
      console.error('❌ Error loading user images:', error);
      console.error('Error details:', {
        name: error instanceof Error ? error.name : 'Unknown',
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined
      });
      setUserImages([]);
    } finally {
      setLoadingImages(false);
      console.log('✅ Finished loading user images');
    }
  };

  const loadGeneratedReels = async () => {
    if (!user?.userId) {
      console.log('❌ No user ID available for loading reels');
      return;
    }
    
    try {
      console.log('🔄 Starting to load generated reels for user:', user.userId);
      const response = await reelGeneratorAPI.getGeneratedReels(user.userId);
      console.log('📡 Generated Reels API response:', response);
      
      if (response.success) {
        const reels = response.reels || [];
        const mappedReels: GeneratedReel[] = reels.map((reel: any) => ({
          id: reel.id ?? reel.name ?? crypto.randomUUID(),
          title: reel.title ?? reel.name ?? 'Untitled Reel',
          prompt: reel.prompt ?? 'Generated from images',
          filename: reel.filename ?? reel.name ?? 'unknown.mp4',
          cloud_path: reel.cloud_path ?? reel.name ?? '',
          blob_path: reel.blob_path ?? '', // ✅ added
          public_url: reel.public_url ?? '',
          images_count: reel.images_count ?? 0,
          created_at: reel.created_at ?? new Date().toISOString(),
          file_size: reel.file_size ?? (reel.file_size_mb ? reel.file_size_mb * 1024 * 1024 : 0), // ✅ added, converts MB → bytes if needed
          file_size_mb: reel.file_size_mb ?? (reel.file_size ? reel.file_size / (1024 * 1024) : 0),
          status: reel.status ?? 'completed',
          description: reel.description ?? '',
          duration_seconds: reel.duration_seconds ?? 0,
          user_id: user.userId,
          kaarigar_id: '',
          video_type: 'generated_reel',
          optimized_prompt: reel.optimized_prompt ?? '',
          selected_image_ids: reel.selected_image_ids ?? [],
          generated_at: reel.generated_at ?? reel.created_at ?? new Date().toISOString(),
          is_active: reel.is_active ?? true,
        }));


        setGeneratedReels(mappedReels);
        console.log(`🎬 Successfully loaded ${mappedReels.length} generated reels:`, mappedReels);
      } else {
        console.error('❌ Failed to load generated reels:', response.error);
        setGeneratedReels([]);
      }
    } catch (error) {
      console.error('❌ Error loading generated reels:', error);
      console.error('Error details:', {
        name: error instanceof Error ? error.name : 'Unknown',
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined
      });
      setGeneratedReels([]);
    } finally {
      console.log('✅ Finished loading generated reels');
    }
  };

  const loadAllUserVideos = async () => {
    try {
      setLoadingAllVideos(true);
      const response = await reelGeneratorAPI.getGeneratedReels(user?.userId || '');
      console.log('📡 Generated Reels for modal response:', response);
      
      if (response.success) {
        const reels = response.reels || [];
        setAllVideos(reels);
        setIsVideosModalOpen(true);
      } else {
        console.error('❌ Failed to load generated reels for modal:', response.error);
        setAllVideos([]);
        setIsVideosModalOpen(true);
      }
    } catch (error) {
      console.error('Failed to load generated reels for modal:', error);
      setAllVideos([]);
      setIsVideosModalOpen(true);
    } finally {
      setLoadingAllVideos(false);
    }
  };

  const handleDeleteVideo = async (videoId: string, videoName: string, cloudPath?: string) => {
    if (!confirm(`Are you sure you want to delete "${videoName}"?`)) {
      return;
    }

    if (!user?.userId) {
      alert('Please log in to delete videos');
      return;
    }

    try {
      console.log(`🗑️ Deleting video: ${videoName} (ID: ${videoId})`);
      
      const response = await reelGeneratorAPI.deleteVideo(videoId, user.userId, cloudPath);
      
      if (response.success) {
        // Remove from local state
        setAllVideos(prev => prev.filter(vid => vid.id !== videoId));
        console.log(`✅ Video deleted successfully: ${response.message}`);
        alert(`Video "${videoName}" deleted successfully!`);
      } else {
        console.error('❌ Delete failed:', response.error);
        alert(`Failed to delete video: ${response.error}`);
      }
    } catch (error) {
      console.error('❌ Delete error:', error);
      alert('Failed to delete video. Please try again.');
    }
  };

  const handleImageSelect = (imageId: string) => {
    console.log('🖼️ Image selection changed:', imageId);
    console.log('Current selected IDs:', selectedImageIds);
    
    setSelectedImageIds(prev => {
      const newSelection = prev.includes(imageId) 
        ? prev.filter(id => id !== imageId)
        : [...prev, imageId];
      
      console.log('New selection:', newSelection);
      return newSelection;
    });
  };

  const handleSelectAll = () => {
    console.log('🔄 Select all triggered');
    console.log('Current selection:', selectedImageIds);
    console.log('Available images:', userImages.length);
    
    if (selectedImageIds.length === userImages.length) {
      console.log('📤 Deselecting all images');
      setSelectedImageIds([]);
    } else {
      console.log('📥 Selecting all images');
      setSelectedImageIds(userImages.map(img => img.id));
    }
  };


  const handleSuggestScript = async () => {
    if (!user?.userId) {
      setGenerationStatus('error');
      setGenerationMessage('Please log in to use AI suggestions');
      return;
    }

    if (!prompt.trim()) {
      setGenerationStatus('error');
      setGenerationMessage('Please enter a prompt first');
      return;
    }

    try {
      setSuggestingScript(true);
      setGenerationStatus('idle');
      setGenerationMessage('');

      console.log('🤖 Starting AI script suggestion process...');
      console.log('📝 Prompt:', prompt);
      console.log('🖼️ Selected image IDs:', selectedImageIds);
      console.log('👤 User ID:', user.userId);

      console.log('🔄 Getting image URLs for selected images...');
      const selectedImages = userImages.filter(img => selectedImageIds.includes(img.id));
      const imageUrls = selectedImages.map(img => img.public_url);
      console.log('🔗 Image URLs:', imageUrls);

      console.log('📡 Calling reelGeneratorAPI.suggestScript...');
      const response = await reelGeneratorAPI.suggestScript({
        prompt: prompt.trim(),
        imageUrls: imageUrls
      }, user.userId);

      console.log('📡 Reel Generator API response:', response);

      if (response.success) {
        const suggestions = Array.isArray((response as any).suggestions)
          ? (response as any).suggestions as string[]
          : (Array.isArray((response as any).ideas) ? (response as any).ideas as string[] : []);
        setScriptSuggestions(suggestions);
        setShowSuggestions(true);
        setGenerationStatus('success');
        setGenerationMessage(`Generated ${suggestions.length} AI script suggestions!`);
        console.log('✅ Script suggestions generated successfully:', suggestions);
      } else {
        setGenerationStatus('error');
        setGenerationMessage(response.error || 'Failed to generate script suggestions');
        console.error('❌ Script suggestion failed:', response.error);
      }
    } catch (error) {
      console.error('❌ Script suggestion error:', error);
      console.error('Error details:', {
        name: error instanceof Error ? error.name : 'Unknown',
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined
      });
      
      setGenerationStatus('error');
      setGenerationMessage(error instanceof Error ? error.message : 'Script suggestion failed');
    } finally {
      setSuggestingScript(false);
      console.log('✅ Finished script suggestion process');
    }
  };

  const handleSuggestionSelect = (suggestion: string) => {
    setSelectedSuggestion(suggestion);
    setPrompt(suggestion);
    setShowSuggestions(false);
    console.log('✅ Selected suggestion:', suggestion);
  };

  const handleGenerateReel = async () => {
    if (!user?.userId) {
      setGenerationStatus('error');
      setGenerationMessage('Please log in to generate reels');
      return;
    }

    if (selectedImageIds.length === 0) {
      setGenerationStatus('error');
      setGenerationMessage('Please select at least one image');
      return;
    }

    if (!reelTitle.trim()) {
      setGenerationStatus('error');
      setGenerationMessage('Please enter a title for your reel');
      return;
    }

    if (!prompt.trim()) {
      setGenerationStatus('error');
      setGenerationMessage('Please enter a prompt');
      return;
    }

    try {
      setGenerating(true);
      setGenerationStatus('idle');
      setGenerationMessage('');

      console.log('🎬 Starting reel generation process...');
      console.log('📝 Prompt:', prompt);
      console.log('🖼️ Selected image IDs:', selectedImageIds);
      console.log('👤 User ID:', user.userId);

      console.log('🔄 Getting image URLs for selected images...');
      const selectedImages = userImages.filter(img => selectedImageIds.includes(img.id));
      const imageUrls = selectedImages.map(img => img.public_url);
      console.log('🔗 Image URLs:', imageUrls);

      console.log('📡 Calling reelGeneratorAPI.generateReel...');
      const response = await reelGeneratorAPI.generateReel({
        prompt: prompt.trim(),
        title: reelTitle.trim(),
        imageUrls: imageUrls
      }, user.userId);

      console.log('📡 Reel Generator API response:', response);

      if (response.success) {
        setGenerationStatus('success');
        setGenerationMessage(`Reel "${reelTitle}" generated successfully!`);
        console.log('✅ Reel generated successfully:', response);
        const url = (response as any).generated_video_url || (response as any).public_url;
        if (typeof url === 'string' && url.length > 0) {
          setResultVideoUrl(url);
        }
        
        // Refresh the generated reels list
        console.log('🔄 Refreshing generated reels list...');
        loadGeneratedReels();
        
        // Reset form
        setSelectedImageIds([]);
        setPrompt('');
        setSelectedSuggestion(null);
        console.log('🔄 Form reset completed');
        
        // Call onComplete if provided
        if (onComplete) {
          console.log('🔄 Calling onComplete callback...');
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
      console.error('❌ Reel generation error:', error);
      console.error('Error details:', {
        name: error instanceof Error ? error.name : 'Unknown',
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined
      });
      
      setGenerationStatus('error');
      setGenerationMessage(error instanceof Error ? error.message : 'Reel generation failed');
    } finally {
      setGenerating(false);
      console.log('✅ Finished reel generation process');
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
      <div className="w-full mt-10 flex justify-between items-center p-3">
        <div className="flex items-center">
          <button
            className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white"
            onClick={onBack}
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div className="text-md font-bold ml-3">Create Reel from Images</div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadAllUserVideos}
            disabled={loadingAllVideos}
            className="flex items-center gap-2"
          >
            <FileVideo className="w-4 h-4" />
            {loadingAllVideos ? 'Loading...' : 'Generated Reels'}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage('create-content/videos2')}
            className="flex items-center gap-2"
          >
            <FileEdit className="w-4 h-4" />
            Edit Video
          </Button>
        </div>
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
            {/* Image Selection */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                Select Images from Media *
              </label>
              <Button
                onClick={() => setIsImageModalOpen(true)}
                variant="outline"
                className="w-full"
                disabled={generating}
              >
                <ImageIcon className="w-4 h-4 mr-2" />
                {selectedImageIds.length === 0 ? 'Choose Images' : `${selectedImageIds.length} Images Selected`}
              </Button>
              {selectedImageIds.length > 0 && (
                <div className="mt-2 text-sm text-gray-600">
                  Selected {selectedImageIds.length} image(s) from your media
                </div>
              )}
            </div>

            {/* Title Input */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                Reel Title *
              </label>
              <Input
                value={reelTitle}
                onChange={(e) => setReelTitle(e.target.value)}
                placeholder="Enter a title for your reel..."
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

            {/* AI Script Suggestion Button */}
            <Button
              onClick={handleSuggestScript}
              disabled={suggestingScript || !prompt.trim()}
              variant="outline"
              className="w-full"
            >
              {suggestingScript ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Generating AI Suggestions...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Suggest AI Script
                </>
              )}
            </Button>

            {/* AI Script Suggestions */}
            {showSuggestions && scriptSuggestions.length > 0 && (
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">
                  AI Script Suggestions:
                </label>
                {scriptSuggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestionSelect(suggestion)}
                    className={`w-full p-3 text-left border rounded-md transition-all ${
                      selectedSuggestion === suggestion
                        ? 'border-purple-500 bg-purple-50'
                        : 'border-gray-200 hover:border-purple-300'
                    }`}
                  >
                    <div className="text-sm font-medium text-gray-900 mb-1">
                      Suggestion {index + 1}
                    </div>
                    <div className="text-xs text-gray-600">
                      {suggestion}
                    </div>
                  </button>
                ))}
              </div>
            )}

            {/* Generate Button */}
            <Button
              onClick={handleGenerateReel}
              disabled={generating || selectedImageIds.length === 0 || !prompt.trim()}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white"
            >
              {generating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Generating Reel...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
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

            {/* Generated Video Preview */}
            {resultVideoUrl && (
              <div className="mt-4">
                <label className="text-sm font-medium text-gray-700 mb-2 block">Generated Video</label>
                <video
                  controls
                  src={resultVideoUrl}
                  className="w-full max-w-2xl border border-gray-200 rounded"
                />
                <div className="mt-3 flex gap-2">
                  <Button
                    onClick={() => {
                      // The video is already saved to Firestore during generation
                      alert('Video has been automatically saved to your media library!');
                    }}
                    className="flex items-center gap-2"
                  >
                    <FileVideo className="w-4 h-4" />
                    Video Saved to Media
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => window.open(resultVideoUrl, '_blank')}
                    className="flex items-center gap-2"
                  >
                    <Play className="w-4 h-4" />
                    Open in New Tab
                  </Button>
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
                        {formatDate(reel.created_at)}
                      </div>
                      <div className="flex items-center gap-1">
                        <ImageIcon className="w-3 h-3" />
                        {reel.images_count} images
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
              <ImageIcon className="w-5 h-5 text-purple-600" />
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
                  <div className="text-sm text-gray-600">
                    <p>Select images to include in your reel ({selectedImageIds.length} selected)</p>
                    <div className="flex gap-2 mt-1">
                      <Badge variant="outline" className="text-xs">
                        {userImages.filter(img => img.type === 'uploaded').length} Uploaded
                      </Badge>
                      <Badge variant="secondary" className="text-xs">
                        {userImages.filter(img => img.type === 'edited').length} AI Edited
                      </Badge>
                    </div>
                  </div>
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
                        <div className="flex items-center gap-1 mt-1">
                          {image.type === 'edited' && (
                            <Badge variant="secondary" className="text-xs px-1 py-0">
                              AI Edited
                            </Badge>
                          )}
                          {image.type === 'uploaded' && (
                            <Badge variant="outline" className="text-xs px-1 py-0">
                              Uploaded
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Videos Modal */}
      <Dialog open={isVideosModalOpen} onOpenChange={setIsVideosModalOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileVideo className="w-5 h-5 text-purple-600" />
              Your Generated Reels
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {loadingAllVideos ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
                <span className="ml-2 text-gray-600">Loading videos...</span>
              </div>
            ) : allVideos.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <FileVideo className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No generated reels found.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-96 overflow-y-auto">
                {allVideos.map((reel: any, idx: number) => (
                  <div key={`${reel.id || reel.name || idx}-${idx}`} className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow">
                    {/* Video Thumbnail */}
                    <div className="relative aspect-video bg-gray-100">
                      <video
                        src={reel.public_url}
                        className="w-full h-full object-cover"
                        poster={reel.thumbnail_url || ''}
                        onError={(e) => {
                          // Fallback to a placeholder if video fails to load
                          e.currentTarget.style.display = 'none';
                          const nextEl = e.currentTarget.nextElementSibling as HTMLElement | null;
                          if (nextEl) {
                            nextEl.style.display = 'flex';
                          }
                        }}
                      />
                      <div className="absolute inset-0 bg-gray-200 flex items-center justify-center" style={{ display: 'none' }}>
                        <FileVideo className="w-12 h-12 text-gray-400" />
                      </div>
                      
                      {/* Play overlay */}
                      <div className="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-30 transition-all flex items-center justify-center">
                        <Button
                          size="sm"
                          variant="secondary"
                          className="opacity-0 hover:opacity-100 transition-opacity"
                          onClick={() => window.open(reel.public_url, '_blank')}
                        >
                          <Play className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                    
                    {/* Video Info */}
                    <div className="p-3">
                      <div className="flex items-start justify-between mb-2">
                        <div className="min-w-0 flex-1">
                          <h3 className="text-sm font-medium text-gray-900 truncate mb-1">
                            {reel.title || reel.name || 'Untitled Reel'}
                          </h3>
                          <p className="text-xs text-gray-500 mb-1">
                            {reel.prompt ? reel.prompt.substring(0, 50) + '...' : 'Generated reel'}
                          </p>
                          <p className="text-xs text-gray-400">
                            {reel.file_size_mb ? `${reel.file_size_mb}MB` : ''} • {reel.images_count || 0} images
                          </p>
                        </div>
                      </div>
                      
                      {/* Action Buttons */}
                      <div className="flex items-center justify-between gap-2">
                        <Button 
                          size="sm" 
                          onClick={() => window.open(reel.public_url, '_blank')}
                          className="flex items-center gap-1 flex-1"
                        >
                          <Play className="w-3 h-3" />
                          Play
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDeleteVideo(
                            reel.id, 
                            reel.title || reel.name || 'Untitled Reel',
                            reel.cloud_path
                          )}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ReelMaker;

