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
} from 'lucide-react';
import { useState } from 'react';
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

type Message = {
  sender: "user" | "ai";
  text: string;
};

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


  const handleAttachImages = (files: FileList | null) => {
    if (!files) return;
    const fileArray = Array.from(files);
    setAttachedImages((prev) => [...prev, ...fileArray]);
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
        {subAction === 'createVideo' && (
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" className="flex flex-col items-center">
                <Upload />
                <span className="mt-2">Attach Images</span>
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-72">
              <Card>
                <CardTitle className="p-3 text-sm">Your Images</CardTitle>
                <CardContent>
                  <input
                    type="file"
                    multiple
                    accept="image/*"
                    onChange={(e) => handleAttachImages(e.target.files)}
                  />
                  <div className="mt-3 grid grid-cols-3 gap-2">
                    {attachedImages.map((file, idx) => (
                      <img
                        key={idx}
                        src={URL.createObjectURL(file)}
                        alt="preview"
                        className="w-20 h-20 object-cover rounded-md border"
                      />
                    ))}
                  </div>
                </CardContent>
              </Card>
            </PopoverContent>
          </Popover>
        )}

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

        {subAction === 'editImage' && (
          <div className="grid grid-cols-2 gap-3">
            {['/sample1.png', '/sample2.png', '/sample3.png', '/sample4.png'].map(
              (img, i) => (
                <div
                  key={i}
                  onClick={() => setSelectedImage(i)}
                  className={`border-2 rounded-md overflow-hidden cursor-pointer ${selectedImage === i ? 'border-blue-400' : 'border-gray-300'
                    }`}
                >
                  <img
                    src={img}
                    alt="Sample"
                    className="w-32 h-32 object-cover"
                  />
                </div>
              )
            )}
          </div>
        )}

        {subAction === 'createImage' && (
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
        )}

      </div>

      {/* Final Next Button */}
      <div className="flex justify-center mt-8 mb-6">
        <Button
          className="bg-blue-600 hover:bg-blue-500 text-white px-8 py-3 rounded-md"
          onClick={handleNext}
        >
          Next
        </Button>
      </div>
    </div>
  );

}

const CreateLogo = () => {
  const { setCurrentPage } = usePage();
  const [isMuted, setIsMuted] = useState(false);
  const [selectedLogo, setSelectedLogo] = useState<number | null>(null);

  const messages: Message[] = [
    { sender: "ai", text: "Hi there 👋 Welcome to Conversational Onboarding!" },
    { sender: "ai", text: "I'm your assistant for setting things up easily." },
    { sender: "user", text: "Hey! Sounds good, what do I need to do?" },
    { sender: "ai", text: "We’ll start by connecting your account and adding your first product." },
    { sender: "user", text: "Alright, let’s go!" },
  ];

  const logos = [
    "/ai_gen_logo.jpeg",
    "/ai_gen_logo.jpeg",
    "/ai_gen_logo.jpeg",
    "/ai_gen_logo.jpeg",
  ];

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
              onClick={() => setSelectedLogo(idx)}
              className={`flex items-center justify-center rounded-xl border-2 p-1 transition ${selectedLogo === idx ? 'border-blue-500 bg-blue-300' : 'border-gray-600 border-dashed'}`}
            >
              <img src={logo} alt={`logo-${idx}`} className="max-h-32 max-w-full" />
            </button>
          ))}
        </div>

        {/* "Make this my logo" button */}
        {selectedLogo !== null && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2">
            <Button className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-md">
              MAKE THIS MY LOGO
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
  const [selectedProduct, setSelectedProduct] = useState<string | null>(null);
  const [useProductMedia, setUseProductMedia] = useState(false);

  const products = ["Product 1", "Product 2", "Product 3"];
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

      <div className='flex flex-col px-5 mt-1'>
        <div className='text-sm font-semibold'>Select the type of Video</div>
        <RadioGroup defaultValue="option-one" className='text-xs flex flex-col gap-1 mt-2'>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="option-one" id="option-one" />
            <Label htmlFor="option-one">Vertical 16:9 (Reels, Shorts)</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="option-two" id="option-two" />
            <Label htmlFor="option-two">Horizontal 9:16 (YouTube Ads)</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="option-three" id="option-three" />
            <Label htmlFor="option-two">Custom (Masti nahi rukni chahiye)</Label>
          </div>
        </RadioGroup>
      </div>

      <div className="flex flex-col px-5 mt-5">
        <div className="text-sm font-semibold mb-2">Select Product (optional)</div>

        {/* Command box */}
        <Command className="rounded-lg border shadow-sm w-full max-w-md bg-white">
          <CommandInput placeholder="Search for a product..." className="text-xs" />
          <CommandEmpty>No Products Found</CommandEmpty>

          <CommandGroup heading="Products">
            {products.map((product, idx) => (
              <CommandItem
                key={idx}
                onSelect={() => setSelectedProduct(product)}
                className={`cursor-pointer text-xs ${selectedProduct === product
                  ? "bg-blue-100 text-blue-700"
                  : "hover:bg-gray-100"
                  }`}
              >
                <span>{product}</span>
              </CommandItem>
            ))}
          </CommandGroup>
        </Command>

        {/* Show selected product */}
        {selectedProduct && (
          <div className="mt-3 flex flex-col items-center gap-2 text-sm w-full">
            <div className='w-full flex justify-start items-center gap-2'>
              <span className="text-gray-600">Selected:</span>
              <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-md font-medium">
                {selectedProduct}
              </span>
            </div>


            <div className="flex items-center gap-2 text-xs">
              <input
                id="useProductMedia"
                type="checkbox"
                checked={useProductMedia}
                onChange={(e) => setUseProductMedia(e.target.checked)}
                className="w-4 h-4 accent-blue-600 cursor-pointer"
              />
              <label
                htmlFor="useProductMedia"
                className="text-gray-700 cursor-pointer"
              >
                Use {selectedProduct}'s photos and videos to generate video
              </label>
            </div>
          </div>
        )}

        <Button variant={'outline'} className='mt-5' onClick={() => setCurrentPage('create-content/videos2')}>Start Creating Video <ArrowRight /></Button>

      </div>
    </div>

  )
}

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