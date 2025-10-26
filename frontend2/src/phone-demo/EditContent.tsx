import { usePage } from '@/contexts/PageContext';
import CreateContent from './CreateContent';
import VideoEditorPreview from '@/components/custom/VideoEditorPreview'
import { House, Send } from 'lucide-react'


const EditContent = () => {
  const { currentPage } = usePage();
  
    // Handle subroutes
    switch (currentPage) {
      case 'create-content':
        return <CreateContent />; // default create content screen
      case 'edit-content/images':
        return <EditImage />;
      case 'edit-content/videos':
        return <EditVideo />;
      
    }
  return (
    <div>EditContent</div>
  )
}

export default EditContent


import { useState } from "react";
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';

const EditImage = () => {
  const { setCurrentPage } = usePage();
  const [image, setImage] = useState("/placeholder.png"); // your current image
  const [prompt, setPrompt] = useState("");

  const suggestions = ["Brighten", "Contrast", "Blur", "Add Filter", "Remove Background"];

  const handleEdit = () => {
    // logic to edit image based on prompt
    console.log("Editing image with prompt:", prompt);
  };

  const handleDownload = () => {
    const link = document.createElement("a");
    link.href = image;
    link.download = "edited-image.png";
    link.click();
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
        <div className="text-md font-bold ml-3">Edit Image</div>
      </div>

      {/* Image Preview */}
      <div className="w-full flex justify-center mt-5">
        <img src={image} alt="Editable" className="max-w-[80%] max-h-[400px] object-contain border border-gray-300 rounded-md" />
      </div>

      {/* Suggestions */}
      <div className="mt-5 px-5">
        <Label className="font-semibold mb-2">Suggestions:</Label>
        <div className="flex gap-2 flex-wrap text-sm">
          {suggestions.map((s) => (
            <button
              key={s}
              className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300"
              onClick={() => setPrompt(s)}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Prompt input */}
      <div className="mt-5 px-5 flex gap-2 items-center">
        <Input
          type="text"
          className="flex-1 border border-gray-300 rounded-md p-2 text-sm"
          placeholder="Enter edit prompt..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />
        <button
          className="px-2 py-2 bg-blue-500 text-white rounded-md"
          onClick={handleEdit}
        >
          <Send size={18} />
        </button>
      </div>

      {/* Download button */}
      <div className="mt-5 px-5 flex justify-end">
        <button
          className="px-4 py-2 bg-green-500 text-white rounded-md"
          onClick={handleDownload}
        >
          Save & Download
        </button>
      </div>
    </div>
  );
};



const EditVideo = () => {
  const { setCurrentPage } = usePage();
  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
      style={{ backgroundImage: "url('/white_bg.png')" }}
    >
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3">
        <button className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white" onClick={() => setCurrentPage('home')}><House /></button>
        <div className="text-md font-bold ml-3">Edit Video</div>
      </div>

      <div className="bg-[#1e1e1e] text-white  shadow-lg p-4 w-full max-w-2xl mx-auto">
              <VideoEditorPreview />
            </div>
    </div>
  )
}