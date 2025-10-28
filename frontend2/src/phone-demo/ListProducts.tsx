import { Button } from "@/components/ui/button";
import { useState } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { usePage } from "@/contexts/PageContext";
import { Facebook, House, Pencil, Plus, ImagePlus, Loader2, Send } from "lucide-react";
import { Input } from "@/components/ui/input";

const ListProducts = () => {
  const { currentPage } = usePage();

  switch (currentPage) {
    case 'list-products':
      return <ListContentMain />; // default create content screen
    case 'list-products/whatsapp-campaign':
      return <WhatsappCampaign />;
    case 'list-products/add-products':
      return <AddProduct />
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
          <Button variant={"outline"} className="text-xs" onClick={()=> setCurrentPage('list-products/add-products')}>
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




import { Trash } from "lucide-react";


type Variant = {
  color: string;
  size: string;
  price: string;
  stock: string;
  image?: File;
};

const AddProduct = () => {
  const { setCurrentPage } = usePage();
  const [name, setName] = useState("");
  const [images, setImages] = useState<File[]>([]);
  const [variants, setVariants] = useState<Variant[]>([
    { color: "", size: "", price: "", stock: "", image: undefined },
  ]);

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setImages((prev) => [...prev, ...Array.from(e.target.files!)]);
    }
  };

  const handleVariantChange = <K extends keyof Variant>(
    index: number,
    key: K,
    value: Variant[K]
  ) => {
    const updated = [...variants];
    updated[index][key] = value;
    setVariants(updated);
  };

  const handleVariantImageUpload = (
    e: React.ChangeEvent<HTMLInputElement>,
    index: number
  ) => {
    if (e.target.files && e.target.files[0]) {
      const updated = [...variants];
      updated[index].image = e.target.files[0];
      setVariants(updated);
    }
  };

  const addVariant = () =>
    setVariants([
      ...variants,
      { color: "", size: "", price: "", stock: "", image: undefined },
    ]);

  const removeVariant = (index: number) =>
    setVariants((prev) => prev.filter((_, i) => i !== index));

  const saveProduct = () => {
    const productData = {
      name,
      images,
      variants,
    };
    console.log("Product saved:", productData);
    alert("Product saved successfully!");
    setCurrentPage("home");
  };

  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
      style={{ backgroundImage: "url('/white_bg.png')" }}
    >
      <div className="w-full mt-10 flex justify-start items-center p-3">
        <button
          className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white"
          onClick={() => setCurrentPage("home")}
        >
          <House />
        </button>
        <div className="text-md font-bold ml-3">Add a New Product</div>
      </div>

      <div className="px-4 pb-10">
        <div className="my-2 flex flex-col gap-1">
          <Label>Name of product</Label>
          <Input
            placeholder="Kurti"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>

        <div className="my-4 flex flex-col gap-1">
          <Label>Upload Product Images</Label>
          <Input type="file" multiple accept="image/*" onChange={handleImageUpload} />
          <div className="flex flex-wrap gap-2 mt-2">
            {images.map((img, idx) => (
              <img
                key={idx}
                src={URL.createObjectURL(img)}
                alt="preview"
                className="w-20 h-20 object-cover rounded-lg border"
              />
            ))}
          </div>
        </div>

        <div className="my-4">
          <Label>Variants</Label>
          {variants.map((variant, index) => (
            <div
              key={index}
              className="flex flex-col gap-2 my-3 p-2 rounded-md border"
            >
              <div className="flex flex-wrap gap-2 items-center">
                <Input
                  placeholder="Color"
                  value={variant.color}
                  onChange={(e) =>
                    handleVariantChange(index, "color", e.target.value)
                  }
                />
                <Input
                  placeholder="Size"
                  value={variant.size}
                  onChange={(e) =>
                    handleVariantChange(index, "size", e.target.value)
                  }
                />
                <Input
                  placeholder="Price"
                  value={variant.price}
                  onChange={(e) =>
                    handleVariantChange(index, "price", e.target.value)
                  }
                />
                <Input
                  placeholder="Stock"
                  value={variant.stock}
                  onChange={(e) =>
                    handleVariantChange(index, "stock", e.target.value)
                  }
                />
                <Button
                  variant="destructive"
                  size="icon"
                  onClick={() => removeVariant(index)}
                >
                  <Trash size={16} />
                </Button>
              </div>

              <div className="flex flex-col">
                <Label className="text-sm text-gray-700">Variant Image</Label>
                <Input
                  type="file"
                  accept="image/*"
                  onChange={(e) => handleVariantImageUpload(e, index)}
                />
                {variant.image && (
                  <img
                    src={URL.createObjectURL(variant.image)}
                    alt="variant preview"
                    className="w-24 h-24 mt-2 object-cover rounded-md border"
                  />
                )}
              </div>
            </div>
          ))}

          <Button onClick={addVariant} variant="secondary" className="mt-2">
            <Plus size={16} className="mr-1" /> Add Variant
          </Button>
        </div>

        <Button
          onClick={saveProduct}
          className="w-full mt-6 "
        >
          Save Product
        </Button>
      </div>
    </div>
  );
};


