import { Button } from "@/components/ui/button";
import { useState } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { usePage } from "@/contexts/PageContext";
import { Facebook, House, Pencil, Plus, ImagePlus, Loader2, Send, Upload, X, Check, Trash } from "lucide-react";
import { Input } from "@/components/ui/input";
import { productAPI, mediaAPI, type CreateProductRequest } from "@/lib/api";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";

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
  const [loading, setLoading] = useState(false);
  const [products, setProducts] = useState<any[]>([]);

  const loadProducts = async () => {
    try {
      setLoading(true);
      const res = await productAPI.list();
      if (res.success) setProducts(res.products);
    } catch (e) {
      console.error('Failed to load products', e);
    } finally {
      setLoading(false);
    }
  };

  // Load on mount
  // eslint-disable-next-line react-hooks/rules-of-hooks
  useState(() => { loadProducts(); return undefined; });
  
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
          {loading && (
            <div className="text-sm text-gray-500 px-2 py-3">Loading products...</div>
          )}
          {!loading && products.length === 0 && (
            <div className="text-sm text-gray-500 px-2 py-3">No products yet. Click Add Product to create one.</div>
          )}
          {products.map((p) => (
            <Button key={p.id} className="bg-white text-black w-full flex justify-between h-15" variant={"outline"}>
              <div className="flex items-center gap-2">
                {/* Thumbnail: first image url if present */}
                <img src={(p.image_urls && p.image_urls[0]) || "pot.webp"} className="h-10 w-10 rounded-md object-cover" />
                <div className="text-left">
                  <div className="font-medium">{p.name}</div>
                  {p.price ? <div className="text-xs">{p.currency || 'INR'} {p.price}</div> : null}
                </div>
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

      <div className="flex flex-col gap-4 mt-4 px-4 mb-10">
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







type Variant = {
  description: string;
  color: string;
  size: string;
  price: string;
  stock: string;
  imageUrl?: string;
  videoUrl?: string;
};

const AddProduct = () => {
  const { setCurrentPage } = usePage();
  // Product Level Fields
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [stock, setStock] = useState("");
  const [productImageUrls, setProductImageUrls] = useState<string[]>([]);
  const [productVideoUrls, setProductVideoUrls] = useState<string[]>([]);
  
  // Variants
  const [variants, setVariants] = useState<Variant[]>([
    { description: "", color: "", size: "", price: "", stock: "", imageUrl: undefined, videoUrl: undefined },
  ]);
  const [availableImages, setAvailableImages] = useState<{id:string;title:string;public_url:string}[]>([]);
  const [availableVideos, setAvailableVideos] = useState<{id:string;title:string;public_url:string}[]>([]);
  const [saving, setSaving] = useState(false);
  
  // Image Choice Dialog States
  const [showImageChoiceDialog, setShowImageChoiceDialog] = useState(false);
  const [imageChoiceMode, setImageChoiceMode] = useState<'product' | 'variant'>('product');
  const [currentVariantIndex, setCurrentVariantIndex] = useState<number>(-1);
  const [currentMediaType, setCurrentMediaType] = useState<'image' | 'video'>('image');
  
  // Upload Dialog States
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<{[key: string]: boolean}>({});
  
  // Select Existing Dialog States
  const [showSelectDialog, setShowSelectDialog] = useState(false);

  const loadMediaChoices = async () => {
    try {
      const res = await productAPI.media();
      if (res.success) {
        setAvailableImages(res.images);
        setAvailableVideos(res.videos);
      }
    } catch (e) {
      console.error('Failed to load media', e);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setUploadingFiles(Array.from(e.target.files));
    }
  };

  const handleUploadMedia = async () => {
    if (uploadingFiles.length === 0) return;
    
    setUploading(true);
    const newProgress: {[key: string]: boolean} = {};
    
    try {
      const uploadedUrls: string[] = [];
      
      for (const file of uploadingFiles) {
        newProgress[file.name] = false;
        setUploadProgress({...newProgress});
        
        const response = await mediaAPI.uploadMedia({
          file,
          media_type: currentMediaType,
          title: file.name
        });
        
        if (response.success && response.public_url) {
          uploadedUrls.push(response.public_url);
        }
        
        newProgress[file.name] = true;
        setUploadProgress({...newProgress});
      }
      
      // Add uploaded media to product or variant
      if (imageChoiceMode === 'product') {
        if (currentMediaType === 'image') {
          setProductImageUrls(prev => [...prev, ...uploadedUrls]);
        } else {
          setProductVideoUrls(prev => [...prev, ...uploadedUrls]);
        }
      } else if (currentVariantIndex >= 0) {
        const updated = [...variants];
        if (uploadedUrls.length > 0) {
          if (currentMediaType === 'image') {
            updated[currentVariantIndex].imageUrl = uploadedUrls[0];
          } else {
            updated[currentVariantIndex].videoUrl = uploadedUrls[0];
          }
        }
        setVariants(updated);
      }
      
      // Reload media after upload
      await loadMediaChoices();
      
      // Close dialog and reset
      setShowUploadDialog(false);
      setUploadingFiles([]);
      setUploadProgress({});
    } catch (e) {
      console.error('Upload failed', e);
      alert('Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };
  
  const handleChooseImage = (mode: 'product' | 'variant', variantIndex: number = -1, mediaType: 'image' | 'video' = 'image') => {
    setImageChoiceMode(mode);
    setCurrentVariantIndex(variantIndex);
    setCurrentMediaType(mediaType);
    setShowImageChoiceDialog(true);
    loadMediaChoices();
  };
  
  const handleSelectExistingImage = (mediaUrl: string) => {
    if (imageChoiceMode === 'product') {
      if (currentMediaType === 'image') {
        setProductImageUrls(prev => [...prev, mediaUrl]);
      } else {
        setProductVideoUrls(prev => [...prev, mediaUrl]);
      }
    } else if (currentVariantIndex >= 0) {
      const updated = [...variants];
      if (currentMediaType === 'image') {
        updated[currentVariantIndex].imageUrl = mediaUrl;
      } else {
        updated[currentVariantIndex].videoUrl = mediaUrl;
      }
      setVariants(updated);
    }
    setShowSelectDialog(false);
    setShowImageChoiceDialog(false);
  };
  
  const removeProductImage = (index: number) => {
    setProductImageUrls(prev => prev.filter((_, i) => i !== index));
  };

  const removeProductVideo = (index: number) => {
    setProductVideoUrls(prev => prev.filter((_, i) => i !== index));
  };

  // load once
  // eslint-disable-next-line react-hooks/rules-of-hooks
  useState(() => { loadMediaChoices(); return undefined; });

  const handleVariantChange = <K extends keyof Variant>(
    index: number,
    key: K,
    value: Variant[K]
  ) => {
    const updated = [...variants];
    updated[index][key] = value;
    setVariants(updated);
  };

  const addVariant = () =>
    setVariants([
      ...variants,
      { description: "", color: "", size: "", price: "", stock: "", imageUrl: undefined, videoUrl: undefined },
    ]);

  const removeVariant = (index: number) =>
    setVariants((prev) => prev.filter((_, i) => i !== index));

  const saveProduct = async () => {
    if (!name.trim()) {
      alert('Please enter product name');
      return;
    }
    try {
      setSaving(true);
      const payload: CreateProductRequest = {
        name: name.trim(),
        description: description.trim(),
        price: price ? parseFloat(price) : undefined,
        stock: stock ? parseInt(stock) : undefined,
        currency: "INR",
        variants: variants.map(v => ({ 
          description: v.description,
          color: v.color, 
          size: v.size, 
          price: v.price, 
          stock: v.stock,
          image_url: v.imageUrl,
          video_url: v.videoUrl
        })),
        image_urls: productImageUrls,
        video_urls: productVideoUrls,
      };
      const res = await productAPI.create(payload);
      if (res.success) {
        alert('Product created');
        setCurrentPage('list-products');
      } else {
        alert(res.error || 'Failed to create product');
      }
    } catch (e) {
      console.error('Create product failed', e);
      alert('Failed to create product');
    } finally {
      setSaving(false);
    }
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

        <div className="my-2 flex flex-col gap-1">
          <Label>Product Description</Label>
          <Input
            placeholder="Beautiful handcrafted kurti..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>

        <div className="my-2 flex flex-col gap-1">
          <Label>Product Price (Base)</Label>
          <Input
            type="number"
            placeholder="1999"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
          />
        </div>

        <div className="my-2 flex flex-col gap-1">
          <Label>Product Stock (Total)</Label>
          <Input
            type="number"
            placeholder="100"
            value={stock}
            onChange={(e) => setStock(e.target.value)}
          />
        </div>

        <div className="my-4 flex flex-col gap-2">
          <Label>Product Images</Label>
          <Button 
            variant="outline" 
            className="flex gap-2 items-center justify-center"
            onClick={() => handleChooseImage('product', -1, 'image')}
          >
            <ImagePlus className="w-4 h-4" />
            Choose Image
          </Button>
          
          {/* Display selected product images */}
          {productImageUrls.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {productImageUrls.map((url, idx) => (
                <div key={idx} className="relative">
                  <img
                    src={url}
                    alt="product"
                    className="w-20 h-20 object-cover rounded-lg border"
                  />
                  <Button
                    variant="destructive"
                    size="icon"
                    className="absolute -top-2 -right-2 h-6 w-6 rounded-full"
                    onClick={() => removeProductImage(idx)}
                  >
                    <X className="w-3 h-3" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="my-4 flex flex-col gap-2">
          <Label>Product Videos</Label>
          <Button 
            variant="outline" 
            className="flex gap-2 items-center justify-center"
            onClick={() => handleChooseImage('product', -1, 'video')}
          >
            <ImagePlus className="w-4 h-4" />
            Choose Video
          </Button>
          
          {/* Display selected product videos */}
          {productVideoUrls.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {productVideoUrls.map((url, idx) => (
                <div key={idx} className="relative">
                  <video
                    src={url}
                    className="w-32 h-20 object-cover rounded-lg border"
                    controls
                  />
                  <Button
                    variant="destructive"
                    size="icon"
                    className="absolute -top-2 -right-2 h-6 w-6 rounded-full"
                    onClick={() => removeProductVideo(idx)}
                  >
                    <X className="w-3 h-3" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="my-4">
          <Label>Variants</Label>
          {variants.map((variant, index) => (
            <div
              key={index}
              className="flex flex-col gap-2 my-3 p-2 rounded-md border"
            >
              <div className="flex flex-col gap-2 mb-2">
                <Label className="text-sm">Variant Description</Label>
                <Input
                  placeholder="e.g., Red XL cotton kurti"
                  value={variant.description}
                  onChange={(e) =>
                    handleVariantChange(index, "description", e.target.value)
                  }
                />
              </div>
              
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
                  type="number"
                  placeholder="Price"
                  value={variant.price}
                  onChange={(e) =>
                    handleVariantChange(index, "price", e.target.value)
                  }
                />
                <Input
                  type="number"
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

              <div className="flex flex-col gap-1">
                <Label className="text-sm text-gray-700">Variant Image</Label>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleChooseImage('variant', index, 'image')}
                  className="flex gap-2"
                >
                  <ImagePlus className="w-4 h-4" />
                  Choose Image
                </Button>
                {variant.imageUrl && (
                  <div className="relative mt-2 w-24">
                    <img
                      src={variant.imageUrl}
                      alt="variant preview"
                      className="w-24 h-24 object-cover rounded-md border"
                    />
                    <Button
                      variant="destructive"
                      size="icon"
                      className="absolute -top-2 -right-2 h-6 w-6 rounded-full"
                      onClick={() => {
                        const updated = [...variants];
                        updated[index].imageUrl = undefined;
                        setVariants(updated);
                      }}
                    >
                      <X className="w-3 h-3" />
                    </Button>
                  </div>
                )}
              </div>

              <div className="flex flex-col gap-1">
                <Label className="text-sm text-gray-700">Variant Video</Label>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleChooseImage('variant', index, 'video')}
                  className="flex gap-2"
                >
                  <ImagePlus className="w-4 h-4" />
                  Choose Video
                </Button>
                {variant.videoUrl && (
                  <div className="relative mt-2 w-32">
                    <video
                      src={variant.videoUrl}
                      className="w-32 h-20 object-cover rounded-md border"
                      controls
                    />
                    <Button
                      variant="destructive"
                      size="icon"
                      className="absolute -top-2 -right-2 h-6 w-6 rounded-full"
                      onClick={() => {
                        const updated = [...variants];
                        updated[index].videoUrl = undefined;
                        setVariants(updated);
                      }}
                    >
                      <X className="w-3 h-3" />
                    </Button>
                  </div>
                )}
              </div>
            </div>
          ))}

          <Button onClick={addVariant} variant="secondary" className="mt-2">
            <Plus size={16} className="mr-1" /> Add Variant
          </Button>
        </div>

        <Button onClick={saveProduct} className="w-full mt-6 " disabled={saving}>
          {saving ? 'Saving...' : 'Save Product'}
        </Button>
      </div>

      {/* Image/Video Choice Dialog - Shows "Upload" or "Select Existing" options */}
      <Dialog open={showImageChoiceDialog} onOpenChange={setShowImageChoiceDialog}>
        <DialogContent className="max-w-[80%]">
          <DialogHeader>
            <DialogTitle>Choose {currentMediaType === 'image' ? 'Image' : 'Video'}</DialogTitle>
            <DialogDescription>
              Upload a new {currentMediaType} or select from existing {currentMediaType}s
            </DialogDescription>
          </DialogHeader>
          
          <div className="flex flex-col gap-3 p-4">
            <Button
              variant="outline"
              className="h-16 flex items-center justify-center gap-2 text-base"
              onClick={() => {
                setShowImageChoiceDialog(false);
                setShowUploadDialog(true);
              }}
            >
              <Upload className="w-5 h-5" />
              Upload New {currentMediaType === 'image' ? 'Image' : 'Video'}
            </Button>
            
            <Button
              variant="outline"
              className="h-16 flex items-center justify-center gap-2 text-base"
              onClick={() => {
                setShowImageChoiceDialog(false);
                setShowSelectDialog(true);
              }}
            >
              <ImagePlus className="w-5 h-5" />
              Select from Existing {currentMediaType === 'image' ? 'Images' : 'Videos'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Select Existing Media Dialog */}
      <Dialog open={showSelectDialog} onOpenChange={setShowSelectDialog}>
        <DialogContent className="max-w-[90%] max-h-[80%] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Select {currentMediaType === 'image' ? 'Image' : 'Video'}</DialogTitle>
            <DialogDescription>
              Choose from your uploaded {currentMediaType}s
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid grid-cols-3 gap-2 p-4">
            {currentMediaType === 'image' ? (
              availableImages.length === 0 ? (
                <div className="col-span-3 text-center text-gray-500 py-8">
                  No images available. Upload some images first.
                </div>
              ) : (
                availableImages.map(img => (
                  <button
                    key={img.id}
                    onClick={() => handleSelectExistingImage(img.public_url)}
                    className="border-2 border-gray-200 rounded-lg p-1 hover:border-blue-500 transition"
                  >
                    <img src={img.public_url} className="w-full h-24 object-cover rounded" />
                    <div className="text-[10px] mt-1 line-clamp-1">{img.title}</div>
                  </button>
                ))
              )
            ) : (
              availableVideos.length === 0 ? (
                <div className="col-span-3 text-center text-gray-500 py-8">
                  No videos available. Upload some videos first.
                </div>
              ) : (
                availableVideos.map(vid => (
                  <button
                    key={vid.id}
                    onClick={() => handleSelectExistingImage(vid.public_url)}
                    className="border-2 border-gray-200 rounded-lg p-1 hover:border-blue-500 transition"
                  >
                    <video src={vid.public_url} className="w-full h-24 object-cover rounded" />
                    <div className="text-[10px] mt-1 line-clamp-1">{vid.title}</div>
                  </button>
                ))
              )
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Upload Media Dialog */}
      <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
        <DialogContent className="max-w-[90%] max-h-[80%] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Upload {currentMediaType === 'image' ? 'Images' : 'Videos'}</DialogTitle>
            <DialogDescription>
              Select {currentMediaType} files to upload
            </DialogDescription>
          </DialogHeader>
          
          <div className="flex flex-col gap-4 p-4">
            {/* File Input */}
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <Input
                type="file"
                multiple
                accept={currentMediaType === 'image' ? 'image/*' : 'video/*'}
                onChange={handleFileSelect}
                className="mb-2"
              />
              <p className="text-sm text-gray-500">
                Select one or more {currentMediaType} files
              </p>
            </div>

            {/* File Preview */}
            {uploadingFiles.length > 0 && (
              <div className="space-y-2">
                <Label>Selected Files ({uploadingFiles.length})</Label>
                <div className="max-h-40 overflow-y-auto space-y-2">
                  {uploadingFiles.map((file, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        {currentMediaType === 'image' ? (
                          <img 
                            src={URL.createObjectURL(file)} 
                            alt={file.name}
                            className="w-10 h-10 object-cover rounded"
                          />
                        ) : (
                          <video 
                            src={URL.createObjectURL(file)} 
                            className="w-16 h-10 object-cover rounded"
                          />
                        )}
                        <span className="text-sm truncate">{file.name}</span>
                      </div>
                      {uploadProgress[file.name] !== undefined && (
                        <div className="ml-2">
                          {uploadProgress[file.name] ? (
                            <Check className="w-5 h-5 text-green-600" />
                          ) : (
                            <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                          )}
                        </div>
                      )}
                      {!uploading && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setUploadingFiles(prev => prev.filter((_, i) => i !== idx))}
                        >
                          <X className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Upload Button */}
            <div className="flex gap-2 justify-end">
              <Button
                variant="outline"
                onClick={() => {
                  setShowUploadDialog(false);
                  setUploadingFiles([]);
                  setUploadProgress({});
                }}
                disabled={uploading}
              >
                Cancel
              </Button>
              <Button
                onClick={handleUploadMedia}
                disabled={uploadingFiles.length === 0 || uploading}
                className="flex gap-2"
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    Upload {uploadingFiles.length} file{uploadingFiles.length !== 1 ? 's' : ''}
                  </>
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};


