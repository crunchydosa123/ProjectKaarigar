import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Image, 
  Loader2, 
  CheckCircle, 
  XCircle, 
  ArrowLeft,
  Clock,
  FileImage,
  ImageIcon,
  Sparkles,
  Wand2,
  Palette
} from 'lucide-react';
import { mediaAPI, imageGenAPI, type MediaItem, type ImageGenerationRequest, type GeneratedImage } from '@/lib/api';
import { usePage } from '@/contexts/PageContext';

interface ImageGeneratorProps {
  onBack: () => void;
  onComplete?: () => void;
}

const ImageGenerator: React.FC<ImageGeneratorProps> = ({ onBack, onComplete }) => {
  const {setCurrentPage} = usePage();
  const [prompt, setPrompt] = useState('');
  const [title, setTitle] = useState('');
  const [aspectRatio, setAspectRatio] = useState('1:1');
  const [referenceImageId, setReferenceImageId] = useState('');
  const [generating, setGenerating] = useState(false);
  const [generationStatus, setGenerationStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [generationMessage, setGenerationMessage] = useState('');
  const [generatedImages, setGeneratedImages] = useState<GeneratedImage[]>([]);
  const [loadingImages, setLoadingImages] = useState(true);
  const [loadingGeneratedImages, setLoadingGeneratedImages] = useState(true);
  const [userImages, setUserImages] = useState<MediaItem[]>([]);
  const [allImages, setAllImages] = useState<any[]>([]); // Combined uploaded + generated images
  const [selectedReferenceImage, setSelectedReferenceImage] = useState<any | null>(null);
  const [isReferenceDropdownOpen, setIsReferenceDropdownOpen] = useState(false);

  // Load user images and generated images on component mount
  useEffect(() => {
    loadUserImages();
    loadGeneratedImages();
  }, []);

  // Combine uploaded and generated images whenever either changes
  useEffect(() => {
    const combinedImages = [
      ...userImages.map(img => ({ ...img, type: 'uploaded' })),
      ...generatedImages.map(img => ({ ...img, type: 'generated' }))
    ];
    setAllImages(combinedImages);
    console.log(`🔄 Combined images: ${userImages.length} uploaded + ${generatedImages.length} generated = ${combinedImages.length} total`);
  }, [userImages, generatedImages]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (isReferenceDropdownOpen) {
        const target = event.target as Element;
        if (!target.closest('.reference-dropdown')) {
          setIsReferenceDropdownOpen(false);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isReferenceDropdownOpen]);

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

  const loadGeneratedImages = async () => {
    try {
      setLoadingGeneratedImages(true);
      console.log('🔄 Loading generated images...');
      const response = await imageGenAPI.getGeneratedImages();
      console.log('📡 Generated images response:', response);
      
      if (response.success) {
        setGeneratedImages(response.images);
        console.log(`🎨 Loaded ${response.images.length} generated images:`, response.images);
      } else {
        console.error('Failed to load generated images:', response.error);
      }
    } catch (error) {
      console.error('Error loading generated images:', error);
    } finally {
      setLoadingGeneratedImages(false);
    }
  };

  const handleReferenceImageSelect = (image: any) => {
    setSelectedReferenceImage(image);
    setReferenceImageId(image.id);
    setIsReferenceDropdownOpen(false);
  };

  const handleClearReferenceImage = () => {
    setSelectedReferenceImage(null);
    setReferenceImageId('');
  };

  const handleGenerateImage = async () => {
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

      console.log('🎨 Starting image generation...');
      console.log('Prompt:', prompt);
      console.log('Title:', title);
      console.log('Aspect ratio:', aspectRatio);
      console.log('Reference image ID:', referenceImageId || 'None');

       const response = await imageGenAPI.generateImage({
         prompt: prompt.trim(),
         title: title.trim(),
         aspect_ratio: aspectRatio,
         reference_image_id: referenceImageId || undefined
       });

      if (response.success) {
        setGenerationStatus('success');
        setGenerationMessage(`Image "${response.title}" generated successfully!`);
        console.log('✅ Image generated successfully:', response);
        
         // Reset form
         setPrompt('');
         setTitle('');
         setReferenceImageId('');
         setSelectedReferenceImage(null);
        
        // Refresh the generated images list
        console.log('🔄 Refreshing generated images list...');
        await loadGeneratedImages();
        
        // Call onComplete if provided
        if (onComplete) {
          setTimeout(() => {
            onComplete();
          }, 2000);
        }
      } else {
        setGenerationStatus('error');
        setGenerationMessage(response.error || 'Image generation failed');
        console.error('❌ Image generation failed:', response.error);
      }
    } catch (error) {
      setGenerationStatus('error');
      setGenerationMessage(error instanceof Error ? error.message : 'Image generation failed');
      console.error('❌ Image generation error:', error);
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

  const getAspectRatioLabel = (ratio: string) => {
    const ratios: { [key: string]: string } = {
      '1:1': 'Square (1:1)',
      '16:9': 'Widescreen (16:9)',
      '9:16': 'Portrait (9:16)',
      '4:3': 'Standard (4:3)',
      '3:4': 'Portrait (3:4)',
      '2:3': 'Portrait (2:3)',
      '3:2': 'Landscape (3:2)'
    };
    return ratios[ratio] || ratio;
  };

  return (
    <div className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
         style={{ backgroundImage: "url('/white_bg.png')" }}>
      
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3">
        <button
          className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white"
          onClick={()=> setCurrentPage('create-content')}
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="text-md font-bold ml-3">Generate Images with AI</div>
      </div>

      <div className="px-4 py-4 space-y-4">
        {/* Generation Form */}
        <Card className="p-4">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-600" />
              Generate New Image
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Title Input */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                Image Title *
              </label>
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter image title"
                disabled={generating}
                className="w-full"
              />
            </div>


            {/* Prompt Input */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                Image Prompt *
              </label>
              <Textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe the image you want to generate... (e.g., 'A beautiful sunset over mountains with a lake in the foreground')"
                rows={3}
                disabled={generating}
                className="w-full"
              />
            </div>

            {/* Aspect Ratio Selection */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                Aspect Ratio
              </label>
              <Select value={aspectRatio} onValueChange={setAspectRatio} disabled={generating}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select aspect ratio" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1:1">Square (1:1)</SelectItem>
                  <SelectItem value="16:9">Widescreen (16:9)</SelectItem>
                  <SelectItem value="9:16">Portrait (9:16)</SelectItem>
                  <SelectItem value="4:3">Standard (4:3)</SelectItem>
                  <SelectItem value="3:4">Portrait (3:4)</SelectItem>
                  <SelectItem value="2:3">Portrait (2:3)</SelectItem>
                  <SelectItem value="3:2">Landscape (3:2)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Reference Image Selection */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                Reference Image (Optional)
              </label>
              <div className="relative reference-dropdown">
                <Button
                  onClick={() => setIsReferenceDropdownOpen(!isReferenceDropdownOpen)}
                  variant="outline"
                  disabled={generating}
                  className="w-full justify-between"
                >
                  <div className="flex items-center gap-2">
                    <Image className="w-4 h-4" />
                    {selectedReferenceImage ? (
                      <span className="truncate">
                        {selectedReferenceImage.title || selectedReferenceImage.original_filename || selectedReferenceImage.filename}
                      </span>
                    ) : (
                      <span>Select Reference Image</span>
                    )}
                  </div>
                  <svg
                    className={`w-4 h-4 transition-transform ${isReferenceDropdownOpen ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </Button>

                {/* Dropdown */}
                {isReferenceDropdownOpen && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto">
                    <div className="p-2">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700">Select from your images:</span>
                        <Button
                          onClick={handleClearReferenceImage}
                          variant="outline"
                          size="sm"
                          className="text-red-600 hover:text-red-700"
                        >
                          Clear
                        </Button>
                      </div>
                      
                      {loadingImages || loadingGeneratedImages ? (
                        <div className="flex items-center justify-center py-4">
                          <Loader2 className="w-4 h-4 animate-spin mr-2" />
                          <span className="text-sm text-gray-600">Loading images...</span>
                        </div>
                      ) : allImages.length === 0 ? (
                        <div className="text-center py-4 text-gray-500">
                          <ImageIcon className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                          <p className="text-sm">No images found. Upload or generate some images first.</p>
                        </div>
                      ) : (
                        <div className="space-y-1">
                          {allImages.map((image) => (
                            <button
                              key={image.id}
                              onClick={() => handleReferenceImageSelect(image)}
                              className={`w-full flex items-center gap-3 p-2 rounded hover:bg-gray-50 transition-colors ${
                                selectedReferenceImage?.id === image.id ? 'bg-blue-50 border border-blue-200' : ''
                              }`}
                            >
                              <img
                                src={image.public_url}
                                alt={image.title || image.original_filename || image.filename}
                                className="w-10 h-10 object-cover rounded"
                              />
                              <div className="flex-1 text-left">
                                <div className="flex items-center gap-2">
                                  <p className="text-sm font-medium text-gray-900 truncate">
                                    {image.title || image.original_filename || image.filename}
                                  </p>
                                  <Badge 
                                    variant={image.type === 'generated' ? 'default' : 'secondary'} 
                                    className="text-xs"
                                  >
                                    {image.type === 'generated' ? 'AI Generated' : 'Uploaded'}
                                  </Badge>
                                </div>
                                <p className="text-xs text-gray-500">
                                  {(image.file_size / 1024).toFixed(1)} KB
                                </p>
                              </div>
                              {selectedReferenceImage?.id === image.id && (
                                <CheckCircle className="w-4 h-4 text-blue-600" />
                              )}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Selected Reference Image Preview */}
              {selectedReferenceImage && (
                <div className="mt-3 p-3 bg-gray-50 rounded border">
                  <div className="flex items-center gap-3">
                    <img
                      src={selectedReferenceImage.public_url}
                      alt={selectedReferenceImage.title || selectedReferenceImage.original_filename || selectedReferenceImage.filename}
                      className="w-16 h-16 object-cover rounded"
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-gray-900">
                          {selectedReferenceImage.title || selectedReferenceImage.original_filename || selectedReferenceImage.filename}
                        </p>
                        <Badge 
                          variant={selectedReferenceImage.type === 'generated' ? 'default' : 'secondary'} 
                          className="text-xs"
                        >
                          {selectedReferenceImage.type === 'generated' ? 'AI Generated' : 'Uploaded'}
                        </Badge>
                      </div>
                      <p className="text-xs text-gray-500">
                        {(selectedReferenceImage.file_size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                    <Button
                      onClick={handleClearReferenceImage}
                      variant="outline"
                      size="sm"
                      className="text-red-600 hover:text-red-700"
                    >
                      Remove
                    </Button>
                  </div>
                </div>
              )}
            </div>

            {/* Generate Button */}
            <Button
              onClick={handleGenerateImage}
              disabled={generating || !prompt.trim() || !title.trim()}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white"
            >
              {generating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Generating Image...
                </>
              ) : (
                <>
                  <Wand2 className="w-4 h-4 mr-2" />
                  Generate Image
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

        {/* Generated Images */}
        <Card className="p-4">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <FileImage className="w-5 h-5 text-purple-600" />
              Generated Images
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loadingGeneratedImages ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
                <span className="ml-2 text-gray-600">Loading generated images...</span>
              </div>
            ) : generatedImages.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <FileImage className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No generated images yet. Create your first AI-generated image above!</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-96 overflow-y-auto">
                {generatedImages.map((image) => (
                  <div
                    key={image.id}
                    className="border border-gray-200 rounded-lg p-3 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-medium text-gray-900 truncate">
                        {image.title}
                      </h3>
                      <div className="flex gap-1">
                        <Badge variant="secondary" className="text-xs">
                          {getAspectRatioLabel(image.aspect_ratio)}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {image.image_type}
                        </Badge>
                      </div>
                    </div>
                    
                    <img
                      src={image.public_url}
                      alt={image.title}
                      className="w-full h-32 object-cover rounded mb-2"
                    />
                    
                    <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                      {image.description || image.prompt}
                    </p>
                    
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatDate(image.generated_at)}
                      </div>
                      <div className="flex items-center gap-1">
                        <Palette className="w-3 h-3" />
                        {(image.file_size / 1024).toFixed(1)} KB
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

    </div>
  );
};

export default ImageGenerator;
