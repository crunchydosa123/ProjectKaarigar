import { Button } from "@/components/ui/button";
import { useState } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { usePage } from "@/contexts/PageContext";
import { Facebook, House, Pencil, Plus, ImagePlus, Loader2, Send } from "lucide-react";

const ListProducts = () => {
  const { currentPage } = usePage();

  switch (currentPage) {
    case 'list-products':
      return <ListContentMain />; // default create content screen
    case 'list-products/whatsapp-campaign':
      return <WhatsappCampaign />;
    case 'list-products/whatsapp-campaign':
      return <WhatsappCampaign />;
    default:
      return <ListContentMain />
  }
}

export default ListProducts;

const ListContentMain = () => {
  const { setCurrentPage } = usePage();
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
        <div className="text-md font-bold ml-3">
          List and Market your Products
        </div>
      </div>

      {/* Listed Products */}
      <div className="px-4">
        <div className="flex justify-between my-2">
          <Label className="mb-1">Your Listed Products</Label>
          <Button variant={"outline"} className="text-xs">
            <Plus /> Add Product
          </Button>
        </div>

        <div className="flex flex-col justify-center gap-1">
          {[
            { img: "pot.webp", name: "Earthen Water Pot" },
            { img: "plant_pot.webp", name: "Potted Plant Pot" },
            { img: "pot.webp", name: "Potted Plant Pot" },
          ].map((item, index) => (
            <Button
              key={index}
              className="bg-white text-black w-full flex justify-between h-15"
              variant={"outline"}
            >
              <div className="flex items-center gap-2">
                <img src={item.img} className="h-10 w-10 rounded-md" />
                <div>{item.name}</div>
              </div>
              <Button variant={"secondary"}>
                <Pencil />
              </Button>
            </Button>
          ))}
        </div>
      </div>

      {/* Marketing Options */}
      <div className="px-4 mt-8 flex flex-col gap-1">
        <Label>Market Products</Label>
        <Button variant={"outline"} className="flex justify-center gap-2" onClick={()=> setCurrentPage('list-products/whatsapp-campaign')}>
          <img src="WhatsApp.webp" className="h-7 w-7" />
          Run a Message Campaign
        </Button>
        <Button variant={"outline"} className="flex justify-center gap-2">
          <img src="yt_shorts.png" className="h-5 w-auto" />
          Post a YouTube Short
        </Button>
        <Button variant={"outline"} className="flex justify-center gap-2">
          <img src="reels.png" className="h-5 w-5" />
          Post an Instagram Reel
        </Button>
      </div>

      {/* Sales by Channel */}
      <div className="px-4 mt-8 flex flex-col gap-2 mb-10">
        <Label>See Sales by Channel</Label>

        <Button
          variant={"outline"}
          className="flex justify-between items-center bg-white text-black w-full"
        >
          <div className="flex items-center gap-2">
            <img src="amazon_logo.png" className="h-6 w-auto" />
            <div>Amazon</div>
          </div>
          <div className="font-semibold">₹12,430</div>
        </Button>

        <Button
          variant={"outline"}
          className="flex justify-between items-center bg-white text-black w-full"
        >
          <div className="flex items-center gap-2">
            <img src="WhatsApp.webp" className="h-6 w-6" />
            <div>WhatsApp</div>
          </div>
          <div className="font-semibold">₹8,720</div>
        </Button>

        <Button
          variant={"outline"}
          className="flex justify-between items-center bg-white text-black w-full"
        >
          <div className="flex items-center gap-2">
            <Facebook className="text-blue-600 h-5 w-5" />
            <div>Facebook</div>
          </div>
          <div className="font-semibold">₹5,350</div>
        </Button>
      </div>
    </div>
  );
}

const WhatsappCampaign = () => {
  const { setCurrentPage } = usePage();

  const [prompt, setPrompt] = useState("");
  const [selectedProduct, setSelectedProduct] = useState("");
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [generatedMessage, setGeneratedMessage] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const usersCount = 47; // placeholder for how many users will receive messages

  const handleGenerateMessage = () => {
    setIsGenerating(true);
    setTimeout(() => {
      setGeneratedMessage(
        `🌿 Check out our new ${selectedProduct || "product"}!\n\n${prompt || "Beautiful handcrafted items available now!"}\n\nOrder now and get 10% off!`
      );
      setIsGenerating(false);
    }, 1500);
  };

  const handleSendMessage = () => {
    setIsSending(true);
    setTimeout(() => {
      alert("Messages sent successfully to all users!");
      setIsSending(false);
    }, 2000);
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
        <div className="text-md font-bold ml-3">Run a Message Campaign</div>
      </div>

      <div className="flex flex-col gap-4 px-2 mt-4 px-4 mb-10">
        {/* Message Prompt */}
        <div>
          <Label>Message Prompt</Label>
          <Textarea
            placeholder="Write the tone or theme of your WhatsApp message..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="mt-1"
          />
        </div>

        {/* Product Dropdown */}
        <div>
          <Label>Select Product</Label>
          <Select onValueChange={(value) => setSelectedProduct(value)}>
            <SelectTrigger className="mt-1">
              <SelectValue placeholder="Choose a product" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Earthen Water Pot">Earthen Water Pot</SelectItem>
              <SelectItem value="Potted Plant Pot">Potted Plant Pot</SelectItem>
              <SelectItem value="Clay Lamp">Clay Lamp</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Image Popover */}
        <div>
          <Label>Add an Image</Label>
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" className="w-full mt-1 flex gap-2">
                <ImagePlus /> {selectedImage ? "Change Image" : "Upload Image"}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="p-4 w-60">
              <input
                type="file"
                accept="image/*"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    const url = URL.createObjectURL(file);
                    setSelectedImage(url);
                  }
                }}
              />
            </PopoverContent>
          </Popover>
          {selectedImage && (
            <img
              src={selectedImage}
              alt="Selected"
              className="h-24 w-24 mt-2 rounded-md object-cover border"
            />
          )}
        </div>

        {/* Generate Message */}
        <Button onClick={handleGenerateMessage} disabled={isGenerating}>
          {isGenerating ? (
            <div className="flex gap-2 items-center">
              <Loader2 className="animate-spin" /> Generating Message...
            </div>
          ) : (
            "Generate Message"
          )}
        </Button>

        {/* Generated Message */}
        {generatedMessage && (
          <div className="bg-white border rounded-md p-3">
            <Label className="text-sm text-gray-700">Generated Message</Label>
            <p className="mt-1 whitespace-pre-line text-sm">{generatedMessage}</p>
          </div>
        )}

        {/* Users Count */}
        <div className="flex justify-between items-center bg-gray-100 border rounded-md p-3 mt-2">
          <span>Users to receive message:</span>
          <span className="font-semibold">{usersCount}</span>
        </div>

        {/* Send Message Button */}
        <Button
          className="mt-2 bg-green-600 hover:bg-green-700 text-white flex gap-2 justify-center items-center"
          onClick={handleSendMessage}
          disabled={isSending}
        >
          {isSending ? (
            <div className="flex gap-2 items-center">
              <Loader2 className="animate-spin" /> Sending to all users...
            </div>
          ) : (
            <>
              <Send /> Send Message to All
            </>
          )}
        </Button>
      </div>
    </div>
  );
};




