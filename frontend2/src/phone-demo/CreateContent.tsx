import { Button } from '@/components/ui/button';
import { usePage } from '@/contexts/PageContext';
import {
  BookImage,
  House,
  ImagePlus,
  Video,
  Image,
  FileEdit,
  Upload,
  ArrowRight, ClosedCaption, Download, Mic, MicOff, Save,
  Loader2,
  Sparkles,
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
import { Select, SelectGroup, SelectItem, SelectLabel } from '@/components/ui/select';
import { SelectContent, SelectTrigger } from '@radix-ui/react-select';
import { RadioGroup, RadioGroupItem } from '@radix-ui/react-radio-group';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from "@/components/ui/command"
import VideoEditorPreview from '@/components/custom/VideoEditorPreview';
import { Input } from '@/components/ui/input';
import { logoAPI, profileAPI, mediaAPI } from "@/lib/api";
import GenerateVideo from './GenerateVideo';
import { Textarea } from '@/components/ui/textarea';


const CreateContent = () => {
  const { currentPage } = usePage();

  // Handle subroutes
  switch (currentPage) {
    case 'create-content':
      return <CreateContentMain />; // default create content screen
    case 'create-content/logos':
      return <CreateLogo />;
    case 'create-content/videos':
      return <CreateVideo />;
    case 'create-content/videos2':
      return <CreateVideo2 />;
    case 'create-content/images':
      return <CreateImage />;
    case 'create-content/generate-video':
      return <GenerateVideo onBack={() => usePage().setCurrentPage('create-content')} />;
    default:
      return <CreateContentMain />
  }
};

export default CreateContent;

const CreateContentMain = () => {
  const { setCurrentPage } = usePage();
  const [activeTab, setActiveTab] = useState<string | null>(null);
  const [subAction, setSubAction] = useState<string | null>(null);
  const [attachedImages, setAttachedImages] = useState<File[]>([]);
  const [selectedImage, setSelectedImage] = useState<number | null>(null);
  const [selectedSuggestion, setSelectedSuggestion] = useState<string>("");
  const [databaseImages, setDatabaseImages] = useState<any[]>([]);
  const [loadingImages, setLoadingImages] = useState(false);


  const handleAttachImages = (files: FileList | null) => {
    if (!files) return;
    const fileArray = Array.from(files);
    setAttachedImages((prev) => [...prev, ...fileArray]);
  };

  const loadDatabaseImages = async () => {
    try {
      setLoadingImages(true);
      console.log('🔧 Starting to load database images...');
      
      // First try to get all media to see what's available
      const allMediaResponse = await mediaAPI.listMedia();
      console.log('🔧 All media response:', allMediaResponse);
      
      // Then get images specifically
      const response = await mediaAPI.listMediaByType('images');
      console.log('🔧 Images response:', response);
      
      if (response.success) {
        setDatabaseImages(response.media);
        console.log(`📁 Loaded ${response.media.length} images from database`);
        console.log('📁 Images data:', response.media);
      } else {
        console.error('Failed to load images:', response.error);
        // Show error message to user
        alert(`Failed to load images: ${response.error}`);
      }
    } catch (error) {
      console.error('Error loading images:', error);
      // Show error message to user
      alert(`Error loading images: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLoadingImages(false);
    }
  };

  const handleNext = () => {
    if (!subAction) return alert('Please select an option first!');
    console.log('User selected:', subAction);
    switch (subAction) {
      case 'createVideo':
        setCurrentPage('create-content/videos');
        break;
      case 'editVideo':
        setCurrentPage('edit-content/videos');
        break;
      case 'createImage':
        setCurrentPage('create-content/images');
        break;
      case 'editImage':
        setCurrentPage('edit-content/images');
        break;
      default:
        setCurrentPage('');
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
        {subAction}
        <div className="text-md font-bold ml-3">Create Content with AI</div>
      </div>

      {/* Main Tabs */}
      <div className="w-full flex justify-center gap-3 px-3 mt-5">
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
      <AnimatePresence>
        {activeTab === 'generate' && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mt-6 flex justify-center gap-3"
          >
            <Button
              className={`w-40 h-24 flex-col ${subAction === 'createVideo' ? 'border-blue-500 border-2' : ''
                }`}
              variant="secondary"
              onClick={() => setSubAction('createVideo')}
            >
              <Video size={36} />
              <div className="mt-1">Create Video</div>
            </Button>
            <Button
              className={`w-40 h-24 flex-col ${subAction === 'createImage' ? 'border-blue-500 border-2' : ''
                }`}
              variant="secondary"
              onClick={() => setSubAction('createImage')}
            >
              <Image size={36} />
              <div className="mt-1">Create Image</div>
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

      {/* Action Section */}
      <div className="mt-8 flex flex-col items-center gap-4">


        {subAction === 'editVideo' && (
          <div className="w-80">
            <Label className="text-sm font-semibold mb-2 block">
              Choose a video to edit:
            </Label>
            <div className="border rounded-md p-3 space-y-2">
              {['PromoVideo.mp4', 'AdClip.mp4', 'DemoFootage.mp4'].map(
                (v, i) => (
                  <Button
                    key={i}
                    className="w-full justify-start"
                    variant="outline"
                    onClick={() => console.log('Edit', v)}
                  >
                    {v}
                  </Button>
                )
              )}
            </div>
          </div>
        )}


        {/*PRATHAM{subAction === 'createImage' && (
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
          className="bg-blue-600 hover:bg-blue-500 w-full text-white px-8 py-3 rounded-md"
          onClick={handleNext}
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

      <Button variant={'outline'} className="p-3 my-5 mx-3" onClick={()=> setCurrentPage('onboarding/profile')}>Next (See Profile) <ArrowRight /></Button>

    </div>
  )
}


type Props = {};

const CreateVideo = (props: Props) => {
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
                        className={`w-full h-24 object-cover border rounded-md cursor-pointer ${
                          referenceMedia === media ? "ring-2 ring-blue-500" : ""
                        }`}
                        onClick={() => handleSelectMedia(media)}
                      />
                    ) : (
                      <img
                        key={media}
                        src={media}
                        alt="placeholder"
                        className={`w-full h-24 object-cover border rounded-md cursor-pointer ${
                          referenceMedia === media ? "ring-2 ring-blue-500" : ""
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



const CreateImage = () => {
  const { setCurrentPage } = usePage();
  const [instructions, setInstructions] = useState("");
  const [referenceImage, setReferenceImage] = useState<string | null>(null);
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [openPopover, setOpenPopover] = useState(false);

  const placeholderImages = [
    "/placeholder.png",
    "/placeholder2.png",
    "/placeholder3.png",
  ];

  const handleSelectImage = (img: string) => {
    setReferenceImage(img);
    setOpenPopover(false);
  };

  const handleGenerate = () => {
    // In real case: call image generation API here
    // For now, just mock it
    setGeneratedImage("/generated_sample.png");
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
        <div className="text-md font-bold ml-3">Create Image</div>
      </div>

      {/* Generated Image Preview */}
        <div className="w-full flex justify-center mt-5">
          <img
            src={generatedImage? "": ""}
            alt="Generated"
            className="max-w-[80%] max-h-[400px] object-contain border border-gray-300 rounded-md"
          />
        </div>

      {/* Instructions */}
      <div className="px-5 mb-5 mt-6">
        <Label className="mb-1">Enter Instructions</Label>
        <Textarea
          className="text-sm mt-2"
          placeholder="Describe what you want to generate..."
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
        />
      </div>

      {/* Image Reference Input */}
      <div className="px-5 mb-5">
        <Label className="mb-1">Insert Image for Reference</Label>
        <Popover open={openPopover} onOpenChange={setOpenPopover}>
          <PopoverTrigger asChild>
            <Button variant="outline" className="mt-2">
              {referenceImage ? "Change Image" : "Add Image"}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-96 p-4">
            <Card>
              <CardHeader>
                <CardTitle>Select or Upload Image</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                <Button
                  variant="outline"
                  onClick={() => alert("Import from device (placeholder)")}
                >
                  Import from device
                </Button>

                <div className="grid grid-cols-3 gap-2">
                  {placeholderImages.map((img) => (
                    <img
                      key={img}
                      src={img}
                      alt="placeholder"
                      className={`w-full h-24 object-cover border rounded-md cursor-pointer ${
                        referenceImage === img ? "ring-2 ring-blue-500" : ""
                      }`}
                      onClick={() => handleSelectImage(img)}
                    />
                  ))}
                </div>
              </CardContent>
            </Card>
          </PopoverContent>
        </Popover>

        {referenceImage && (
          <div className="mt-3">
            <img
              src={referenceImage}
              alt="Reference"
              className="w-48 h-32 object-cover border border-gray-300 rounded-md"
            />
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
  const { setCurrentPage } = usePage();
  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
      style={{ backgroundImage: "url('/white_bg.png')" }}
    >
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3">
        <button className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white" onClick={() => setCurrentPage('home')}><House /></button>
        <div className="text-md font-bold ml-3">Create Video with AI</div>
      </div>

      <div className="bg-[#1e1e1e] text-white  shadow-lg p-4 w-full max-w-2xl mx-auto">
        <VideoEditorPreview />
      </div>

    </div>
  )
}