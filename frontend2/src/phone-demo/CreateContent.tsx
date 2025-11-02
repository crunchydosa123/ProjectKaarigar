import { Button } from '@/components/ui/button';
import { usePage } from '@/contexts/PageContext';
import {
  BookImage,
  House,
  ImagePlus,
  Image,
  FileEdit,
  ArrowRight, ArrowLeft, ClosedCaption, Download, Mic, MicOff, Save,
  Loader2,
  Sparkles,
  CheckCircle,
  XCircle,
  Lightbulb,
  Edit3,
  Wand2
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from '@radix-ui/react-popover';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import VideoEditorPreview from '@/components/custom/VideoEditorPreview';
import { Input } from '@/components/ui/input';
import { logoAPI, profileAPI, mediaAPI, imageGenAPI, imageEditAPI, videoEditAPI, type MediaItem, type GeneratedImage, type ImageSuggestion } from "@/lib/api";
import GenerateVideo from './GenerateVideo';
import ReelMaker from './ReelMaker';
import ImageGenerator from './ImageGenerator';
import { Textarea } from '@/components/ui/textarea';


const CreateContent = () => {
  const { setCurrentPage, currentPage } = usePage();

  // Handle subroutes
  switch (currentPage) {
    case 'create-content':
      return <CreateContentMain />; // default create content screen
    case 'create-content/logos':
      return <CreateLogo />;
    case 'create-content/videos':
      return <ReelMaker onBack={() => setCurrentPage('create-content')} />;
    case 'create-content/videos2':
      return <CreateVideo2 />;
    case 'create-content/images':
      return <ImageGenerator onBack={() => usePage().setCurrentPage('create-content')} />;
    case 'create-content/generate-video':
      return <GenerateVideo onBack={() => usePage().setCurrentPage('create-content')} />;
    case 'create-content/reel-maker':
      return <ReelMaker onBack={() => usePage().setCurrentPage('create-content')} />;
    default:
      return <CreateContentMain />
  }
};

export default CreateContent;

const CreateContentMain = () => {
  const { setCurrentPage, selectedVideo, setSelectedVideo } = usePage();
  const [activeTab, setActiveTab] = useState<string | null>(null);
  const [subAction, setSubAction] = useState<string | null>(null);

  // Edit Image Modal State
  const [selectedImage, setSelectedImage] = useState<MediaItem | GeneratedImage | null>(null);
  const [referenceImage, setReferenceImage] = useState<MediaItem | GeneratedImage | null>(null);
  const [brandLogoUrl, setBrandLogoUrl] = useState<string>('');
  const [usingBrandLogo, setUsingBrandLogo] = useState(false);
  const [showReferencePicker, setShowReferencePicker] = useState(false);
  const [suggestions, setSuggestions] = useState<ImageSuggestion[]>([]);
  const [selectedSuggestion, setSelectedSuggestion] = useState<ImageSuggestion | null>(null);
  const [customPrompt, setCustomPrompt] = useState('');
  const [editTitle, setEditTitle] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [editing, setEditing] = useState(false);
  const [analysisStatus, setAnalysisStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [analysisMessage, setAnalysisMessage] = useState('');
  const [editStatus, setEditStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [editMessage, setEditMessage] = useState('');
  const [allImages, setAllImages] = useState<any[]>([]);
  const [loadingImages, setLoadingImages] = useState(false);

  // Video editing state
  const [userVideos, setUserVideos] = useState<any[]>([]);
  const [loadingVideos, setLoadingVideos] = useState(false);

  // Load all images when edit image is selected
  useEffect(() => {
    if (subAction === 'editImage') {
      loadAllImages();
      loadBrandLogo();
    }
  }, [subAction]);

  // Load brand logo from profile
  const loadBrandLogo = async () => {
    try {
      const response = await profileAPI.getProfileData();
      if (response.success && (response as any).brand_info && (response as any).brand_info.logo_url) {
        setBrandLogoUrl((response as any).brand_info.logo_url);
        console.log("🏷️ Loaded brand logo from profile:", (response as any).brand_info.logo_url);
      } else {
        console.log("⚠️ No brand logo found in profile");
      }
    } catch (error) {
      console.log("⚠️ Could not load brand logo from profile:", error);
    }
  };

  // Load videos when edit video is selected
  useEffect(() => {
    if (subAction === 'editVideo') {
      loadUserVideos();
    }
  }, [subAction]);

  const loadAllImages = async () => {
    try {
      setLoadingImages(true);

      // Load uploaded images
      const uploadedResponse = await mediaAPI.listMediaByType('images');
      const uploadedImages = uploadedResponse.success ? uploadedResponse.media.map(img => ({ ...img, type: 'uploaded' })) : [];

      // Load generated images
      const generatedResponse = await imageGenAPI.getGeneratedImages();
      const generatedImages = generatedResponse.success ? generatedResponse.images.map(img => ({ ...img, type: 'generated' })) : [];

      // Combine all images
      const combinedImages = [...uploadedImages, ...generatedImages];
      setAllImages(combinedImages);

      console.log(`🔄 Loaded ${uploadedImages.length} uploaded + ${generatedImages.length} generated = ${combinedImages.length} total images`);
    } catch (error) {
      console.error('Error loading images:', error);
    } finally {
      setLoadingImages(false);
    }
  };

  const loadUserVideos = async () => {
    try {
      setLoadingVideos(true);
      console.log('CreateContentMain: Loading user videos...');

      const response = await videoEditAPI.getUserVideos();
      console.log('CreateContentMain: Full response:', response);

      if (response.success) {
        setUserVideos(response.videos);
        console.log('CreateContentMain: Set user videos:', response.videos);
      } else {
        console.error('CreateContentMain: Failed to load user videos:', response.error);
        // If it's an auth error, don't show error message, just return
        if (response.error && response.error.includes('authenticated')) {
          console.log('CreateContentMain: User not authenticated, skipping video load');
          return;
        }
      }
    } catch (error) {
      console.error('CreateContentMain: Failed to load user videos:', error);
      // If it's an auth error, don't show error message
      if (error instanceof Error && error.message.includes('401')) {
        console.log('CreateContentMain: Authentication error, skipping video load');
        return;
      }
    } finally {
      setLoadingVideos(false);
    }
  };

  const handleImageSelect = (image: any) => {
    setSelectedImage(image);
    setSuggestions([]);
    setSelectedSuggestion(null);
    setCustomPrompt('');
    setEditTitle('');
    setReferenceImage(null);
    setUsingBrandLogo(false);
    setAnalysisStatus('idle');
    setAnalysisMessage('');
    setEditStatus('idle');
    setEditMessage('');
  };

  const handleReferenceImageSelect = (image: any) => {
    setReferenceImage(image);
    setUsingBrandLogo(false);
    setShowReferencePicker(false);
    console.log("✅ Selected reference image:", image);
  };

  const handleUseBrandLogo = () => {
    if (brandLogoUrl) {
      setReferenceImage(null);
      setUsingBrandLogo(true);
      setShowReferencePicker(false);
      console.log("🏷️ Using brand logo:", brandLogoUrl);
    } else {
      setEditStatus('error');
      setEditMessage('Brand logo not found. Please generate a logo first.');
    }
  };

  const handleClearReferenceImage = () => {
    setReferenceImage(null);
    setUsingBrandLogo(false);
  };

  const handleAnalyzeImage = async () => {
    if (!selectedImage) {
      setAnalysisStatus('error');
      setAnalysisMessage('Please select an image first');
      return;
    }

    try {
      setAnalyzing(true);
      setAnalysisStatus('idle');
      setAnalysisMessage('');

      console.log('🔍 Analyzing image for suggestions...');
      console.log('Image URL:', selectedImage.public_url);

      const response = await imageEditAPI.analyzeImage({
        image_url: selectedImage.public_url
      });

      if (response.success) {
        setSuggestions(response.suggestions);
        setAnalysisStatus('success');
        setAnalysisMessage(`Generated ${response.suggestions.length} creative suggestions!`);
        console.log('✅ Analysis completed:', response.suggestions);
      } else {
        setAnalysisStatus('error');
        setAnalysisMessage(response.error || 'Failed to analyze image');
        console.error('❌ Analysis failed:', response.error);
      }
    } catch (error) {
      setAnalysisStatus('error');
      setAnalysisMessage(error instanceof Error ? error.message : 'Analysis failed');
      console.error('❌ Analysis error:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSuggestionSelect = (suggestion: ImageSuggestion) => {
    setSelectedSuggestion(suggestion);
    setCustomPrompt(suggestion.prompt);
    setEditTitle(`${suggestion.category} - ${suggestion.description}`);
  };

  const handleEditImage = async () => {
    if (!selectedImage) {
      setEditStatus('error');
      setEditMessage('Please select an image first');
      return;
    }

    if (!customPrompt.trim()) {
      setEditStatus('error');
      setEditMessage('Please enter a prompt or select a suggestion');
      return;
    }

    if (!editTitle.trim()) {
      setEditStatus('error');
      setEditMessage('Please enter a title for the edited image');
      return;
    }

    try {
      setEditing(true);
      setEditStatus('idle');
      setEditMessage('');

      console.log('🎨 Editing image...');
      console.log('Image URL:', selectedImage.public_url);
      console.log('Prompt:', customPrompt);
      console.log('Title:', editTitle);
      console.log('Reference Image:', referenceImage ? referenceImage.public_url : 'None');
      console.log('Using Brand Logo:', usingBrandLogo);

      // Check if reference image or brand logo is selected
      const hasReference = referenceImage || usingBrandLogo;

      let response;
      if (hasReference) {
        // Use edit with reference API
        response = await imageEditAPI.editImageWithReference({
          image_url: selectedImage.public_url,
          prompt: customPrompt.trim(),
          title: editTitle.trim(),
          original_image_id: selectedImage.id,
          reference_image_url: referenceImage ? referenceImage.public_url : undefined,
          use_brand_logo: usingBrandLogo
        });
      } else {
        // Use regular edit API
        response = await imageEditAPI.editImage({
          image_url: selectedImage.public_url,
          prompt: customPrompt.trim(),
          title: editTitle.trim(),
          original_image_id: selectedImage.id
        });
      }

      if (response.success) {
        setEditStatus('success');
        const refType = response.reference_image_type ? ` (with ${response.reference_image_type === 'brand_logo' ? 'brand logo' : 'reference image'})` : '';
        setEditMessage(`Image "${response.title}" edited successfully!${refType}`);
        console.log('✅ Image edited successfully:', response);

        // Refresh the images list to show the new edited image
        await loadAllImages();

        // Clear the form
        setCustomPrompt('');
        setEditTitle('');
        setSelectedSuggestion(null);
        setSuggestions([]);
        setReferenceImage(null);
        setUsingBrandLogo(false);
        setAnalysisStatus('idle');
        setAnalysisMessage('');
      } else {
        setEditStatus('error');
        setEditMessage(response.error || 'Image editing failed');
        console.error('❌ Image editing failed:', response.error);
      }
    } catch (error) {
      setEditStatus('error');
      setEditMessage(error instanceof Error ? error.message : 'Image editing failed');
      console.error('❌ Image editing error:', error);
    } finally {
      setEditing(false);
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category.toLowerCase()) {
      case 'branding':
        return 'bg-blue-100 text-blue-800';
      case 'artisanal':
        return 'bg-green-100 text-green-800';
      case 'creative':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const handleNext = () => {
    if (!subAction) return alert('Please select an option first!');
    console.log('User selected:', subAction);
    switch (subAction) {
      case 'editVideo':
        if (!selectedVideo) {
          alert('Please select a video to edit first!');
          return;
        }
        setCurrentPage('create-content/videos2');
        break;
      case 'createImage':
        setCurrentPage('create-content/images');
        break;
      case 'editImage':
        // Modal will be shown in Action Section
        break;
      case 'createReel':
        setCurrentPage('create-content/videos');
        break;
      default:
        setCurrentPage('create-content');
        break;
    }
  };

  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
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
        <div className="text-md font-bold ml-3">Create Content with AI</div>
      </div>

      {/* Main Tabs */}
      <div className="w-full flex justify-center gap-1 px-3 mt-5">
        <Button
          className={`w-1/2 h-32 flex-col transition-all duration-200 ${activeTab === 'generate' ? 'border-blue-500 border-2' : ''
            }`}
          variant={'outline'}
          onClick={() =>
            setActiveTab(activeTab === 'generate' ? null : 'generate')
          }
        >
          <ImagePlus size={40} />
          <div className="mt-2 text-md font-semibold">Generate Content</div>
        </Button>

        <Button
          className={`w-1/2 h-32 flex-col transition-all duration-200 ${activeTab === 'edit' ? 'border-blue-500 border-2' : ''
            }`}
          variant={'outline'}
          onClick={() => setActiveTab(activeTab === 'edit' ? null : 'edit')}
        >
          <BookImage size={40} />
          <div className="mt-2 text-md font-semibold">Edit Content</div>
        </Button>
      </div>

      {/* Sub-options */}
      <div className='px-2'>
        <AnimatePresence>
          {activeTab === 'generate' && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mt-6 flex justify-center gap-1"
            >
              <Button
                className={`w-40 h-24 flex-col ${subAction === 'createImage' ? 'border-blue-500 border-2' : ''
                  }`}
                variant="secondary"
                onClick={() => setSubAction('createImage')}
              >
                <Sparkles size={36} />
                <div className="mt-1">Generate Image</div>
              </Button>
              <Button
                className={`w-40 h-24 flex-col ${subAction === 'createReel' ? 'border-blue-500 border-2' : ''
                  }`}
                variant="secondary"
                onClick={() => setSubAction('createReel')}
              >
                <ImagePlus size={36} />
                <div className="mt-1">Create Reel</div>
              </Button>
            </motion.div>
          )}

          {activeTab === 'edit' && (

            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mt-6 flex justify-center gap-3"
            >
              <Button
                className={`w-40 h-24 flex-col ${subAction === 'editVideo' ? 'border-blue-500 border-2' : ''
                  }`}
                variant="secondary"
                onClick={() => setSubAction('editVideo')}
              >
                <FileEdit size={36} />
                <div className="mt-1">Edit Video</div>
              </Button>
              <Button
                className={`w-40 h-24 flex-col ${subAction === 'editImage' ? 'border-blue-500 border-2' : ''
                  }`}
                variant="secondary"
                onClick={() => setSubAction('editImage')}
              >
                <Image size={36} />
                <div className="mt-1">Edit Image</div>
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Action Section */}
      <div className="mt-8 flex flex-col items-center gap-4">


        {subAction === 'editVideo' && (
          <div className="w-80">
            <div className="flex justify-between items-center mb-2">
              <Label className="text-sm font-semibold">
                Choose a video to edit:
              </Label>
              <button
                onClick={loadUserVideos}
                disabled={loadingVideos}
                className="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
              >
                {loadingVideos ? 'Loading...' : 'Refresh'}
              </button>
            </div>
            <div className="border rounded-md p-3 space-y-2">
              {loadingVideos ? (
                <div className="text-center py-4 text-gray-500">
                  Loading your videos...
                </div>
              ) : userVideos.length > 0 ? (
                userVideos.map((video) => (
                  <Button
                    key={video.id}
                    className={`w-full justify-start ${selectedVideo?.id === video.id ? 'border-blue-500 bg-blue-50' : ''
                      }`}
                    variant="outline"
                    onClick={() => {
                      console.log('Edit video:', video.title);
                      setSelectedVideo(video);
                    }}
                  >
                    <div className="flex items-center gap-2">
                      <video
                        src={video.public_url}
                        className="w-8 h-8 object-cover rounded"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                        }}
                      />
                      <div className="text-left">
                        <div className="font-medium">{video.title}</div>
                        <div className="text-xs text-gray-500 capitalize">{video.type}</div>
                      </div>
                    </div>
                  </Button>
                ))
              ) : (
                <div className="text-center py-4 text-gray-500">
                  No videos found. Upload some videos first!
                </div>
              )}
            </div>

            {/* Selected Video Indicator */}
            {selectedVideo && (
              <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded-md">
                <div className="text-sm font-medium text-blue-800">Selected Video:</div>
                <div className="text-sm text-blue-600">{selectedVideo.title}</div>
                <div className="text-xs text-blue-500 capitalize">{selectedVideo.type}</div>
              </div>
            )}
          </div>
        )}

        {subAction === 'editImage' && (
          <div className="w-full max-w-4xl space-y-4">
            {/* Image Selection */}
            <div className="p-4">
              <div className="text-lg flex items-center gap-2 my-2 font-bold">
                <Image className="w-5 h-5 text-purple-600" />
                Select Image to Edit
              </div>
              <div>
                {loadingImages ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
                    <span className="ml-2 text-gray-600">Loading images...</span>
                  </div>
                ) : allImages.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Image className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                    <p>No images found. Upload or generate some images first.</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-1 gap-4 max-h-60 overflow-y-auto">
                    {allImages.map((image) => (
                      <button
                        key={image.id}
                        onClick={() => handleImageSelect(image)}
                        className={`relative border-2 rounded-lg overflow-hidden transition-all ${selectedImage?.id === image.id
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-gray-200 hover:border-purple-300'
                          }`}
                      >
                        <img
                          src={image.public_url}
                          alt={image.title || (image as any).original_filename || image.filename}
                          className="w-full h-32 object-cover"
                          onError={(e) => {
                            console.error('Image load error:', image.public_url);
                            e.currentTarget.src = '/placeholder-image.png';
                          }}
                        />
                        <div className="absolute top-2 left-2">
                          <Badge
                            variant={(image as any).type === 'generated' ? 'default' : 'secondary'}
                            className="text-xs"
                          >
                            {(image as any).type === 'generated' ? 'AI Generated' : 'Uploaded'}
                          </Badge>
                        </div>
                        {selectedImage?.id === image.id && (
                          <div className="absolute inset-0 bg-purple-500 bg-opacity-20 flex items-center justify-center">
                            <CheckCircle className="w-8 h-8 text-purple-600" />
                          </div>
                        )}
                        <div className="p-2">
                          <p className="text-xs font-medium text-gray-900 truncate">
                            {image.title || (image as any).original_filename || image.filename}
                          </p>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Selected Image Preview and Analysis */}
            {selectedImage && (
              <div className="p-4">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Edit3 className="w-5 h-5 text-purple-600" />
                  Selected Image
                </CardTitle>
                <CardContent>
                  <div className="flex items-center gap-4">
                    <img
                      src={selectedImage.public_url}
                      alt={selectedImage.title || (selectedImage as any).original_filename || selectedImage.filename}
                      className="w-24 h-24 object-cover rounded"
                    />
                    <div className='flex-col'>
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">
                          {selectedImage.title || (selectedImage as any).original_filename || selectedImage.filename}
                        </h3>
                        <Badge
                          variant={(selectedImage as any).type === 'generated' ? 'default' : 'secondary'}
                          className="text-xs mt-1"
                        >
                          {(selectedImage as any).type === 'generated' ? 'AI Generated' : 'Uploaded'}
                        </Badge>
                      </div>
                      <Button
                        onClick={handleAnalyzeImage}
                        disabled={analyzing}
                        className="bg-purple-600 hover:bg-purple-700 text-white text-xs my-1"
                      >
                        {analyzing ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Analyzing...
                          </>
                        ) : (
                          <>
                            <Lightbulb className="w-4 h-4 " />
                            Get AI Suggestions
                          </>
                        )}
                      </Button>
                    </div>
                  </div>

                  {/* Analysis Status */}
                  {analysisMessage && (
                    <div className={`mt-3 p-3 rounded-md flex items-center gap-2 ${analysisStatus === 'success'
                        ? 'bg-green-50 text-green-800 border border-green-200'
                        : 'bg-red-50 text-red-800 border border-red-200'
                      }`}>
                      {analysisStatus === 'success' ? (
                        <CheckCircle className="w-4 h-4" />
                      ) : (
                        <XCircle className="w-4 h-4" />
                      )}
                      {analysisMessage}
                    </div>
                  )}
                </CardContent>
              </div>
            )}

            {/* AI Suggestions */}
            {suggestions.length > 0 && (
              <Card className="p-4">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Lightbulb className="w-5 h-5 text-purple-600" />
                    AI Suggestions ({suggestions.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {suggestions.map((suggestion, index) => (
                      <div
                        key={index}
                        role="button"
                        tabIndex={0}
                        onClick={() => handleSuggestionSelect(suggestion)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            handleSuggestionSelect(suggestion);
                          }
                        }}
                        className={`w-full p-2 text-left border rounded-md transition-all cursor-pointer ${selectedSuggestion === suggestion
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-gray-200 hover:border-purple-300'
                          }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <Badge className={`text-xs ${getCategoryColor(suggestion.category)}`}>
                                {suggestion.category}
                              </Badge>
                              {selectedSuggestion === suggestion && (
                                <CheckCircle className="w-4 h-4 text-purple-600" />
                              )}
                            </div>
                            <p className="text-sm font-medium text-gray-900 mb-1">
                              {suggestion.prompt}
                            </p>
                            <p className="text-xs text-gray-600">
                              {suggestion.description}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Edit Form */}
            {selectedImage && (
              <div className="p-4">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Wand2 className="w-5 h-5 text-purple-600" />
                  Edit Image
                </CardTitle>
                <CardContent className="space-y-4">
                  {/* Title Input */}
                  <div>
                    <Label className="text-sm font-medium text-gray-700 mb-2 block">
                      Edited Image Title *
                    </Label>
                    <Input
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      placeholder="Enter title for edited image"
                      disabled={editing}
                      className="w-full"
                    />
                  </div>

                  {/* Reference Image Section (Optional) */}
                  <div>
                    <Label className="text-sm font-medium text-gray-700 mb-2 block">
                      Reference Image (Optional - for branding)
                    </Label>
                    <div className="space-y-2">
                      <div className="flex gap-2">
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => setShowReferencePicker(!showReferencePicker)}
                          disabled={editing}
                          className="flex-1"
                        >
                          <ImagePlus className="w-4 h-4 mr-2" />
                          Select Reference Image
                        </Button>
                        <Button
                          type="button"
                          variant="outline"
                          onClick={handleUseBrandLogo}
                          disabled={editing || !brandLogoUrl}
                          className="flex-1"
                        >
                          <Sparkles className="w-4 h-4 mr-2" />
                          Use Brand Logo
                        </Button>
                      </div>

                      {/* Reference Image Preview */}
                      {(referenceImage || usingBrandLogo) && (
                        <div className="relative border border-purple-200 rounded-lg p-3 bg-purple-50">
                          <div className="flex items-center gap-3">
                            <img
                              src={usingBrandLogo ? brandLogoUrl : referenceImage?.public_url}
                              alt={usingBrandLogo ? "Brand Logo" : referenceImage?.title || "Reference"}
                              className="w-16 h-16 object-cover rounded"
                              onError={(e) => {
                                e.currentTarget.src = '/placeholder-image.png';
                              }}
                            />
                            <div className="flex-1">
                              <p className="text-sm font-medium text-gray-900">
                                {usingBrandLogo ? "Brand Logo" : (referenceImage?.title || referenceImage?.filename || "Reference Image")}
                              </p>
                              <Badge className="text-xs mt-1 bg-purple-100 text-purple-800">
                                {usingBrandLogo ? "Brand Logo" : "Reference"}
                              </Badge>
                            </div>
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              onClick={handleClearReferenceImage}
                              disabled={editing}
                              className="text-red-600 hover:text-red-700"
                            >
                              <XCircle className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      )}

                      {/* Reference Image Picker */}
                      {showReferencePicker && (
                        <div className="border border-gray-200 rounded-lg p-3 bg-white max-h-48 overflow-y-auto">
                          <div className="flex justify-between items-center mb-2">
                            <Label className="text-xs font-semibold text-gray-600">
                              Select from your images:
                            </Label>
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              onClick={() => setShowReferencePicker(false)}
                              className="h-6 w-6 p-0"
                            >
                              <XCircle className="w-4 h-4" />
                            </Button>
                          </div>
                          <div className="grid grid-cols-3 gap-2">
                            {allImages
                              .filter(img => img.id !== selectedImage?.id) // Don't show the main selected image
                              .slice(0, 9) // Show max 9 images
                              .map((image) => (
                                <button
                                  key={image.id}
                                  type="button"
                                  onClick={() => handleReferenceImageSelect(image)}
                                  className={`relative border-2 rounded-lg overflow-hidden transition-all ${
                                    referenceImage?.id === image.id
                                      ? 'border-purple-500 bg-purple-50'
                                      : 'border-gray-200 hover:border-purple-300'
                                  }`}
                                >
                                  <img
                                    src={image.public_url}
                                    alt={image.title || image.filename}
                                    className="w-full h-20 object-cover"
                                    onError={(e) => {
                                      e.currentTarget.src = '/placeholder-image.png';
                                    }}
                                  />
                                  {referenceImage?.id === image.id && (
                                    <div className="absolute inset-0 bg-purple-500 bg-opacity-20 flex items-center justify-center">
                                      <CheckCircle className="w-6 h-6 text-purple-600" />
                                    </div>
                                  )}
                                </button>
                              ))}
                            {allImages.filter(img => img.id !== selectedImage?.id).length === 0 && (
                              <div className="col-span-3 text-center py-4 text-sm text-gray-500">
                                No other images available
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Prompt Input */}
                  <div>
                    <Label className="text-sm font-medium text-gray-700 mb-2 block">
                      Edit Prompt *
                    </Label>
                    <Textarea
                      value={customPrompt}
                      onChange={(e) => setCustomPrompt(e.target.value)}
                      placeholder="Describe how you want to edit the image..."
                      rows={3}
                      disabled={editing}
                      className="w-full"
                    />
                  </div>

                  {/* Edit Button */}
                  <Button
                    onClick={handleEditImage}
                    disabled={editing || !customPrompt.trim() || !editTitle.trim()}
                    className="w-full bg-purple-600 hover:bg-purple-700 text-white"
                  >
                    {editing ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Editing Image...
                      </>
                    ) : (
                      <>
                        <Wand2 className="w-4 h-4 mr-2" />
                        Edit Image
                      </>
                    )}
                  </Button>

                  {/* Edit Status */}
                  {editMessage && (
                    <div className={`p-3 rounded-md flex items-center gap-2 ${editStatus === 'success'
                        ? 'bg-green-50 text-green-800 border border-green-200'
                        : 'bg-red-50 text-red-800 border border-red-200'
                      }`}>
                      {editStatus === 'success' ? (
                        <CheckCircle className="w-4 h-4" />
                      ) : (
                        <XCircle className="w-4 h-4" />
                      )}
                      {editMessage}
                    </div>
                  )}
                </CardContent>
              </div>
            )}

            {/* Edited Images Display */}
            {allImages.filter(img => (img as any).type === 'generated' && (img as any).image_type === 'edited').length > 0 && (
              <Card className="p-4">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Wand2 className="w-5 h-5 text-purple-600" />
                    Recently Edited Images
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4 max-h-60 overflow-y-auto">
                    {allImages
                      .filter(img => (img as any).type === 'generated' && (img as any).image_type === 'edited')
                      .slice(0, 6) // Show last 6 edited images
                      .map((image) => (
                        <div key={image.id} className="border border-gray-200 rounded-lg p-3 hover:shadow-md transition-shadow">
                          <img
                            src={image.public_url}
                            alt={image.title || image.filename}
                            className="w-full h-24 object-cover rounded mb-2"
                            onError={(e) => {
                              console.error('Image load error:', image.public_url);
                              e.currentTarget.src = '/placeholder-image.png';
                            }}
                          />
                          <div className="text-xs">
                            <p className="font-medium text-gray-900 truncate mb-1">
                              {image.title || image.filename}
                            </p>
                            <p className="text-gray-500 truncate">
                              {(image as any).prompt || 'AI Edited'}
                            </p>
                            <Badge className="text-xs mt-1 bg-purple-100 text-purple-800">
                              Edited
                            </Badge>
                          </div>
                        </div>
                      ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}


        {/*PRATHAM{subAction === 'createImage' && {
          <div className="w-80 flex flex-col items-center gap-5">
            <div className="w-full">
              <Label className="text-sm font-semibold mb-2 block">
                Choose a template:
              </Label>

              <Select onValueChange={(value) => {
                console.log("Template selected:", value);
                setSelectedSuggestion(value);
              }}>
                <SelectTrigger className="w-full border border-gray-300 rounded-md p-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white justify-between">
                  {selectedSuggestion === "" ? <span>Select a suggestion</span> : <Label>{selectedSuggestion}</Label>}
                </SelectTrigger>

                <SelectContent className="bg-white border border-gray-200 rounded-md shadow-md">
                  <SelectGroup>
                    <SelectLabel className="text-gray-500 text-xs px-2 mb-1">Suggestions</SelectLabel>
                    <SelectItem value="ad-banner" className="cursor-pointer hover:bg-blue-50">
                      🪧 Ad Banner
                    </SelectItem>
                    <SelectItem value="discount-banner" className="cursor-pointer hover:bg-blue-50">
                      💸 Discount Banner
                    </SelectItem>
                    <SelectItem value="poster" className="cursor-pointer hover:bg-blue-50">
                      🖼️ Poster
                    </SelectItem>
                    <SelectItem value="social-post" className="cursor-pointer hover:bg-blue-50">
                      📱 Social Media Post
                    </SelectItem>
                    <SelectItem value="event-flyer" className="cursor-pointer hover:bg-blue-50">
                      🎟️ Event Flyer
                    </SelectItem>
                  </SelectGroup>
                </SelectContent>
              </Select>
            </div>

            <div className="w-full">
              <Label className="text-sm font-semibold mb-2 block">
                Describe your image:
              </Label>
              <input
                type="text"
                placeholder="e.g. Summer Sale Banner with bright colors"
                className="w-full border border-gray-300 rounded-md p-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                onChange={(e) => console.log('Description:', e.target.value)}
              />
            </div>
          </div>
        )}*/}

      </div>

      {/* Final Next Button */}
      <div className="flex justify-center mt-8 mb-6 px-5">
        <Button
          className="bg-blue-600 hover:bg-blue-500 w-full text-white px-8 py-3 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={handleNext}
          disabled={subAction === 'editVideo' && !selectedVideo}
        >
          Next
        </Button>
      </div>
    </div>
  );

}

interface LogoGenerationRequest {
  conversation_data: string;
  brand_name?: string;
  language?: string;
}

type LogoMessage = {
  sender: "user" | "ai";
  text: string;
};

const CreateLogo = () => {
  const { setCurrentPage } = usePage();
  const [isMuted, setIsMuted] = useState(false);
  const [selectedLogo, setSelectedLogo] = useState<number | null>(null);
  const [brandName, setBrandName] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedLogos, setGeneratedLogos] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Load brand name from profile data on component mount
  useEffect(() => {
    const fetchBrandName = async () => {
      try {
        const response = await profileAPI.getProfileData();
        if (response.success && (response as any).brand_info && (response as any).brand_info.brand_name) {
          setBrandName((response as any).brand_info.brand_name);
          console.log("🏷️ Loaded brand name from profile:", (response as any).brand_info.brand_name);
        }
      } catch (error) {
        console.log("⚠️ Could not load brand name from profile:", error);
      }
    };

    fetchBrandName();
  }, []);

  const messages: LogoMessage[] = [
    { sender: "ai", text: "Hi there 👋 Welcome to Conversational Onboarding!" },
    { sender: "ai", text: "I'm your assistant for setting things up easily." },
    { sender: "user", text: "Hey! Sounds good, what do I need to do?" },
    { sender: "ai", text: "We’ll start by connecting your account and adding your first product." },
    { sender: "user", text: "Alright, let’s go!" },
  ];

  const defaultLogos = [
    "/ai_gen_logo.jpeg",
    "/ai_gen_logo.jpeg",
    "/ai_gen_logo.jpeg",
    "/ai_gen_logo.jpeg",
  ];

  const logos = generatedLogos.length > 0 ? generatedLogos : defaultLogos;

  const handleGenerateLogo = async () => {
    if (!brandName.trim()) {
      setError("Please enter a brand name");
      return;
    }

    setIsGenerating(true);
    setError("");
    setSuccess("");

    try {
      // Sample conversation data for logo generation
      const conversationData = `
        My brand name is ${brandName}. I am an artisan who creates handmade products.
        I want a logo that represents my craft and brand identity.
        The logo should be modern, clean, and professional.
        It should work well for both digital and print use.
      `;

      const requestData: LogoGenerationRequest = {
        conversation_data: conversationData,
        brand_name: brandName,
        language: "en"
      };

      const response = await logoAPI.generateLogo(requestData);
      console.log("📄 Logo generation response:", response);

      if (response.success && response.logo_url) {
        // Check if the logo URL is not the default fallback
        if (response.logo_url !== "/ai_gen_logo.jpeg" && !response.logo_url.includes("ai_gen_logo")) {
          // Add the new logo to the existing logos array
          setGeneratedLogos(prev => {
            const newLogos = [...prev, response.logo_url!];
            console.log("✅ Generated logo URL:", response.logo_url);
            console.log("📄 Updated logos array:", newLogos);
            return newLogos;
          });
          setSuccess("Logo generated successfully!");
          setSelectedLogo(generatedLogos.length); // Select the newly generated logo
          console.log("🎯 Selected logo index:", generatedLogos.length);
        } else {
          console.warn("⚠️ Received default logo URL, not adding to array");
          console.log("🔍 Logo URL received:", response.logo_url);
          setError("Logo generation returned default image. Please try again.");
        }
      } else {
        console.error("❌ Logo generation failed:", response);
        setError(response.error || "Failed to generate logo. Please try again.");
      }
    } catch (err) {
      console.error("Logo generation error:", err);
      setError("Failed to generate logo. Please check your connection and try again.");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSelectLogo = async () => {
    if (selectedLogo !== null) {
      setIsGenerating(true);
      setError("");
      setSuccess("");

      try {
        const selectedLogoUrl = logos[selectedLogo];
        console.log("🔄 Saving selected logo:", selectedLogoUrl);
        console.log("🏷️ Brand name:", brandName);
        console.log("📊 Debug Info:", {
          selectedLogoIndex: selectedLogo,
          totalLogos: logos.length,
          logoUrl: selectedLogoUrl,
          brandName: brandName
        });

        // First, save the logo URL to Cloud Storage and profiles collection
        const response = await logoAPI.saveLogoUrl(selectedLogoUrl, brandName);

        if (response.success) {
          setSuccess("Logo selected and saved to Cloud Storage and profiles collection!");
          console.log("✅ Logo saved successfully:", response);

          // Also update the profile collection with brand info
          try {
            await profileAPI.updateBrand(brandName, selectedLogoUrl);
            console.log("✅ Brand info also updated in profiles collection");
          } catch (profileError) {
            console.warn("⚠️ Profile update failed, but logo was saved:", profileError);
          }

          // Navigate to profile page after a short delay
          setTimeout(() => {
            setCurrentPage('onboarding/profile');
          }, 1500);
        } else {
          setError(`Failed to save logo: ${response.error || 'Unknown error'}`);
        }
      } catch (err) {
        console.error("Logo save error:", err);
        setError("Failed to save logo. Please check your connection and try again.");
      } finally {
        setIsGenerating(false);
      }
    } else {
      console.warn("⚠️ No logo selected");
      setError("Please select a logo first");
    }
  };

  // Debug function for console
  const debugLogoState = () => {
    console.log("🔍 Logo Debug Info:", {
      generatedLogos: logos,
      selectedLogoIndex: selectedLogo,
      brandName: brandName,
      isGenerating: isGenerating,
      error: error,
      success: success
    });
  };

  // Make debug function available globally for console access
  (window as any).debugLogoState = debugLogoState;

  // Log initial state
  console.log("🎨 CreateLogo component mounted with state:", {
    logos: logos,
    selectedLogo: selectedLogo,
    brandName: brandName,
    isGenerating: isGenerating
  });

  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
      style={{ backgroundImage: "url('/white_bg.png')" }}
    >
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3">
        <button className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white" onClick={() => setCurrentPage('home')}><House /></button>
        <div className="text-md font-bold ml-3">Create Logo with AI</div>
      </div>

      {/* Brand Name Input */}
      <div className="px-4 mb-4">
        <Label className="text-sm font-medium mb-2 block">Enter your brand name</Label>
        <div className="flex gap-2">
          <Input
            type="text"
            placeholder="e.g., Mitti Crafts, Artisan Studio..."
            value={brandName}
            onChange={(e) => setBrandName(e.target.value)}
            className="flex-1"
          />
          <Button
            onClick={handleGenerateLogo}
            disabled={isGenerating || !brandName.trim()}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                Generate
              </>
            )}
          </Button>
        </div>

        {/* Status Messages */}
        {error && (
          <div className="text-red-600 text-sm mt-2 p-2 bg-red-50 rounded">
            {error}
          </div>
        )}
        {success && (
          <div className="text-green-600 text-sm mt-2 p-2 bg-green-50 rounded">
            {success}
          </div>
        )}
      </div>

      <div className="relative w-full h-[300px] bg-gray-800 border overflow-hidden rounded-lg">
        {/* Top bar with buttons */}
        <div className="absolute right-3 flex gap-2 z-10">
          <button className="bg-yellow-500 hover:bg-blue-600 text-white flex justify-center items-center w-10 h-10 text-xs px-3 py-1 rounded-sm shadow">
            <Download />
          </button>
          <button className="bg-green-500 hover:bg-green-600 flex justify-center items-center w-10 h-10 text-white text-xs px-3 py-1 rounded-md shadow">
            <Save />
          </button>
        </div>

        {/* X-axis scale */}
        <div className="pt-5 absolute top-0 left-10 right-0 h-8 flex items-end border-b text-[10px] text-white">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="w-10 text-center border-l border-gray-200">
              {i * 20}
            </div>
          ))}
        </div>

        {/* Y-axis scale */}
        <div className="absolute top-8 bottom-0 left-0 w-10 flex flex-col items-end border-r text-[10px] text-white">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="h-10 border-t border-gray-200 pr-1">
              {i * 20}
            </div>
          ))}
        </div>

        {/* Logo grid */}
        <div className="absolute top-8 left-10 right-0 bottom-0 bg-gray-400 grid grid-cols-2 grid-rows-2 gap-1 pt-4 px-2">
          {logos.map((logo, idx) => (
            <button
              key={idx}
              onClick={() => {
                console.log("🖱️ Logo clicked:", idx, logos[idx]);
                setSelectedLogo(idx);
                console.log("✅ Logo selected:", idx);
              }}
              className={`flex items-center justify-center rounded-xl border-2 p-1 transition ${selectedLogo === idx ? 'border-blue-500 bg-blue-300' : 'border-gray-600 border-dashed'}`}
            >
              <img
                src={logo}
                alt={`logo-${idx}`}
                className="max-h-32 max-w-full object-contain"
                onError={(e) => {
                  console.error(`❌ Failed to load logo ${idx}:`, logo);
                  e.currentTarget.src = "/ai_gen_logo.jpeg"; // Fallback image
                }}
                onLoad={() => {
                  console.log(`✅ Loaded logo ${idx}:`, logo);
                }}
              />
            </button>
          ))}

          {/* Show debug info if no logos */}
          {logos.length === 0 && (
            <div className="col-span-2 row-span-2 flex items-center justify-center text-white text-sm">
              <div className="text-center">
                <div>No logos generated yet</div>
                <div className="text-xs mt-1">Click "Generate Logo" to create your first logo</div>
              </div>
            </div>
          )}
        </div>

        {/* "Make this my logo" button */}
        {selectedLogo !== null && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2">
            <Button
              onClick={handleSelectLogo}
              disabled={isGenerating}
              className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-md disabled:opacity-50"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Saving Logo...
                </>
              ) : (
                "MAKE THIS MY LOGO"
              )}
            </Button>
          </div>
        )}
      </div>

      <Card className="mx-2 py-4 bg-yellow-100 mt-4">
        <CardContent>
          <div className="flex justify-start  text-sm font-bold">Edit and Generate logos using your voice over Conversational AI</div>
          <div className="mt-2 px-5 flex justify-center items-center gap-2">
            <button
              onClick={() => setIsMuted(!isMuted)}
              className={`flex items-center gap-2 p-5 rounded-md transition text-white
                  ${isMuted ? "bg-green-500 hover:bg-green-400" : "bg-red-500 hover:bg-red-400"}`}
            >
              {isMuted ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
            </button>
            <Popover>
              <PopoverTrigger>
                <Button variant="outline" className="w-15 h-15">
                  <ClosedCaption className="w-10 h-10" />
                </Button>
              </PopoverTrigger>

              <PopoverContent
                align="center"
                side="top"
                className="fixed left-1/2 top-1/2 -translate-x-3/4 -translate-y-1/2 w-60 h-80 border-none bg-transparent shadow-none"
              >
                <Card className="w-full h-full flex flex-col">
                  <CardHeader>
                    <CardTitle>Conversation Transcript</CardTitle>
                  </CardHeader>

                  <CardContent className="text-sm flex-1 overflow-y-auto space-y-3 p-2">
                    {messages.map((msg, index) => (
                      <div
                        key={index}
                        className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
                      >
                        <div
                          className={`px-3 py-2 rounded-2xl max-w-[75%] ${msg.sender === "user"
                            ? "bg-blue-600 text-white rounded-br-none"
                            : "bg-gray-200 text-gray-900 rounded-bl-none"
                            }`}
                        >
                          {msg.text}
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </PopoverContent>
            </Popover>
          </div>
        </CardContent>
      </Card>

      <Button variant={'outline'} className="p-3 my-5 mx-3" onClick={() => setCurrentPage('onboarding/profile')}>Next (See Profile) <ArrowRight /></Button>

    </div>
  )
}


const CreateVideo = () => {
  const { setCurrentPage } = usePage();
  const [instructions, setInstructions] = useState("");
  const [referenceMedia, setReferenceMedia] = useState<string | null>(null);
  const [generatedVideo, setGeneratedVideo] = useState<string | null>(null);
  const [openPopover, setOpenPopover] = useState(false);

  const placeholderVideos = [
    "/sample_video1.mp4",
    "/sample_video2.mp4",
    "/placeholder.png", // could include images as references too
  ];

  const handleSelectMedia = (media: string) => {
    setReferenceMedia(media);
    setOpenPopover(false);
  };

  const handleGenerate = () => {
    // Mock generation
    setGeneratedVideo("/generated_sample.mp4");
  };

  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
      style={{ backgroundImage: "url('/white_bg.png')" }}
    >
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3">
        <button
          className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white"
          onClick={() => setCurrentPage("home")}
        >
          <House />
        </button>
        <div className="text-md font-bold ml-3">Create Video</div>
      </div>

      {/* Generated Video Preview */}
      {generatedVideo && (
        <div className="w-full flex justify-center mt-5">
          <video
            controls
            src={generatedVideo}
            className="max-w-[80%] max-h-[400px] object-contain border border-gray-300 rounded-md"
          />
        </div>
      )}

      {/* Instructions */}
      <div className="px-5 mb-5 mt-6">
        <Label className="mb-1">Enter Instructions</Label>
        <Textarea
          className="text-sm mt-2"
          placeholder="Describe the video you want to generate..."
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
        />
      </div>

      {/* Reference Media */}
      <div className="px-5 mb-5">
        <Label className="mb-1">Insert Reference (optional)</Label>
        <Popover open={openPopover} onOpenChange={setOpenPopover}>
          <PopoverTrigger asChild>
            <Button variant="outline" className="mt-2">
              {referenceMedia ? "Change Reference" : "Add Reference"}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-96 p-4">
            <Card>
              <CardHeader>
                <CardTitle>Select or Upload Reference</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                <Button
                  variant="outline"
                  onClick={() => alert("Import from device (placeholder)")}
                >
                  Import from device
                </Button>

                <div className="grid grid-cols-3 gap-2">
                  {placeholderVideos.map((media) =>
                    media.endsWith(".mp4") ? (
                      <video
                        key={media}
                        src={media}
                        className={`w-full h-24 object-cover border rounded-md cursor-pointer ${referenceMedia === media ? "ring-2 ring-blue-500" : ""
                          }`}
                        onClick={() => handleSelectMedia(media)}
                      />
                    ) : (
                      <img
                        key={media}
                        src={media}
                        alt="placeholder"
                        className={`w-full h-24 object-cover border rounded-md cursor-pointer ${referenceMedia === media ? "ring-2 ring-blue-500" : ""
                          }`}
                        onClick={() => handleSelectMedia(media)}
                      />
                    )
                  )}
                </div>
              </CardContent>
            </Card>
          </PopoverContent>
        </Popover>

        {referenceMedia && (
          <div className="mt-3">
            {referenceMedia.endsWith(".mp4") ? (
              <video
                controls
                src={referenceMedia}
                className="w-48 h-32 object-cover border border-gray-300 rounded-md"
              />
            ) : (
              <img
                src={referenceMedia}
                alt="Reference"
                className="w-48 h-32 object-cover border border-gray-300 rounded-md"
              />
            )}
          </div>
        )}
      </div>

      {/* Generate Button */}
      <div className="px-5 mb-10">
        <Button className="w-full" onClick={handleGenerate}>
          Generate
        </Button>
      </div>
    </div>
  );
};




const CreateVideo2 = () => {
  const { setCurrentPage, selectedVideo } = usePage();
  const [selectedVideoUrl, setSelectedVideoUrl] = useState<string>(selectedVideo?.public_url || '/sample-video.mp4');

  // Update selectedVideoUrl when selectedVideo changes
  useEffect(() => {
    if (selectedVideo) {
      setSelectedVideoUrl(selectedVideo.public_url);
    }
  }, [selectedVideo]);

  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
      style={{ backgroundImage: "url('/white_bg.png')" }}
    >
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3">
        <button className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white" onClick={() => setCurrentPage('create-content')}><ArrowLeft /></button>
        <div className="text-md font-bold ml-3">Create Video with AI</div>
      </div>

      {/* Selected Video Info */}
      {selectedVideo && (
        <div className="p-4 mb-4">
          <div className="bg-white rounded-lg p-4 shadow-sm border border-blue-200">
            <h2 className="text-lg font-semibold text-gray-800 mb-2">Selected Video</h2>
            <div className="flex items-center gap-3">
              <video
                src={selectedVideo.public_url}
                className="w-16 h-16 object-cover rounded-lg"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                }}
              />
              <div>
                <p className="font-medium text-gray-800">{selectedVideo.title}</p>
                <p className="text-sm text-gray-600 capitalize">{selectedVideo.type}</p>
                <p className="text-xs text-gray-500">Ready for AI editing</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Video Editor */}
      <div className="flex-1 p-4">
        <div className="bg-[#1e1e1e] text-white shadow-lg p-4 w-full max-w-2xl mx-auto rounded-lg">
          <VideoEditorPreview selectedVideoUrl={selectedVideoUrl} />
        </div>
      </div>
    </div>
  )
}
