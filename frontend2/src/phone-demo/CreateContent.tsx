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
} from 'lucide-react';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from '@radix-ui/react-popover';
import { Card, CardContent, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectGroup, SelectItem, SelectLabel } from '@/components/ui/select';
import { SelectContent, SelectTrigger } from '@radix-ui/react-select';

const CreateContent = () => {
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
    // Example: move to the next module based on user selection
    switch (subAction){
      case 'createVideo': 
        setCurrentPage('create-content/videos');
      case 'editVideo': 
        setCurrentPage('edit-content/videos');
      case 'createImage': 
        setCurrentPage('create-content/images');
      case 'editImage': 
        setCurrentPage('edit-content/images');
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
      <div className="w-full flex justify-center gap-3 px-3 mt-5">
        <Button
          className={`w-1/2 h-32 flex-col transition-all duration-200 ${
            activeTab === 'generate' ? 'border-blue-500 border-2' : ''
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
          className={`w-1/2 h-32 flex-col transition-all duration-200 ${
            activeTab === 'edit' ? 'border-blue-500 border-2' : ''
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
              className={`w-40 h-24 flex-col ${
                subAction === 'createVideo' ? 'border-blue-500 border-2' : ''
              }`}
              variant="secondary"
              onClick={() => setSubAction('createVideo')}
            >
              <Video size={36} />
              <div className="mt-1">Create Video</div>
            </Button>
            <Button
              className={`w-40 h-24 flex-col ${
                subAction === 'createImage' ? 'border-blue-500 border-2' : ''
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
              className={`w-40 h-24 flex-col ${
                subAction === 'editVideo' ? 'border-blue-500 border-2' : ''
              }`}
              variant="secondary"
              onClick={() => setSubAction('editVideo')}
            >
              <FileEdit size={36} />
              <div className="mt-1">Edit Video</div>
            </Button>
            <Button
              className={`w-40 h-24 flex-col ${
                subAction === 'editImage' ? 'border-blue-500 border-2' : ''
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
                  className={`border-2 rounded-md overflow-hidden cursor-pointer ${
                    selectedImage === i ? 'border-blue-400' : 'border-gray-300'
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
};

export default CreateContent;
