import { usePage } from "@/contexts/PageContext"
import { ArrowRight, ClosedCaption, Download, House, Mic, MicOff, Save, Loader2, Sparkles } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@radix-ui/react-popover";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { logoAPI, profileAPI } from "@/lib/api";

// Define the interface locally to avoid import issues
interface LogoGenerationRequest {
  conversation_data: string;
  brand_name?: string;
  language?: string;
}

type Message = {
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

  const messages: Message[] = [
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

export default CreateLogo;
