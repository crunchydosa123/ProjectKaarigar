import { Button } from "@/components/ui/button";
import { useState } from "react";
import { Textarea } from "@/components/ui/textarea";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { usePage } from "@/contexts/PageContext";
import { Facebook, House, Pencil, Plus, ImagePlus, Loader2, Send, Upload, X, Check, Trash, SkipBack, Undo2, ExternalLink } from "lucide-react";
import { Input } from "@/components/ui/input";
import { productAPI, mediaAPI, whatsappAPI, type CreateProductRequest } from "@/lib/api";
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
    case 'list-products/add-listing':
      return <AddListing />
    default:
      return <ListContentMain />
  }
}

export default ListProducts;

const ListContentMain = () => {
  const { setCurrentPage, setSelectedProductId } = usePage();
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
          <Button variant={"outline"} className="text-xs" onClick={() => setCurrentPage('list-products/add-products')}>
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
            <Button
              key={p.id}
              className="bg-white text-black w-full flex justify-between h-15"
              variant={"outline"}
              onClick={() => {
                setSelectedProductId(p.id);
                setCurrentPage('product-detail');
              }}
            >
              <div className="flex items-center gap-2">
                {/* Thumbnail: first image url if present */}
                <img src={(p.image_urls && p.image_urls[0]) || "pot.webp"} className="h-10 w-10 rounded-md object-cover" />
                <div className="text-left">
                  <div className="font-medium">{p.name}</div>
                  {p.price ? <div className="text-xs">{p.currency || 'INR'} {p.price}</div> : null}
                </div>
              </div>
              <Button variant={"secondary"} onClick={(e) => { e.stopPropagation(); /* TODO: Edit inline */ }}>
                <Pencil />
              </Button>
            </Button>
          ))}
        </div>
      </div>
      
      {/*<Button className="mx-4 mt-5" onClick={() => setCurrentPage('list-products/add-listing')}>List a product</Button>*/}

      {/* Marketing Options */}
      <div className="px-4 mt-8 flex flex-col gap-1">
        <Label>Market Products</Label>
        <Button variant={"outline"} className="flex justify-center gap-2" onClick={() => setCurrentPage('list-products/whatsapp-campaign')}>
          <img src="WhatsApp.webp" className="h-7 w-7" />
          Run a Message Campaign
        </Button>
        <Button variant={"outline"} className="flex justify-center gap-2" onClick={() => setCurrentPage('youtube-shorts')}>
          <img src="yt_shorts.png" className="h-5 w-auto" />
          Post a YouTube Short
        </Button>
        <Button variant={"outline"} className="flex justify-center gap-2">
          <img src="reels.png" className="h-5 w-5" />
          Post an Instagram Reel
        </Button>
      </div>

      {/* Marketplace Listings */}
      <div className="px-4 mt-6">
        <Button 
          className="w-full flex justify-center gap-2 bg-orange-600 hover:bg-orange-700 text-white"
          onClick={() => setCurrentPage('marketplace-listings')}
        >
          <ExternalLink className="h-4 w-4" />
          View Marketplace Listings
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
  const [selectedProductData, setSelectedProductData] = useState<any>(null);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [generatedMessage, setGeneratedMessage] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [localImageFile, setLocalImageFile] = useState<File | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [availableImages, setAvailableImages] = useState<{ id: string; title: string; public_url: string }[]>([]);
  const [showImageSelector, setShowImageSelector] = useState(false);
  const [sentResult, setSentResult] = useState<{ notified_count: number; status: string; message: string } | null>(null);

  // Load products on mount
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

  // Load media images
  const loadMedia = async () => {
    try {
      const res = await productAPI.media();
      if (res.success) setAvailableImages(res.images);
    } catch (e) {
      console.error('Failed to load media', e);
    }
  };

  // eslint-disable-next-line react-hooks/rules-of-hooks
  useState(() => { loadProducts(); loadMedia(); return undefined; });

  // When product is selected, auto-select first image
  const handleProductSelect = (productId: string) => {
    setSelectedProduct(productId);
    setSentResult(null);
    const product = products.find(p => p.id === productId);
    setSelectedProductData(product);
    
    // Auto-select first image from product
    if (product?.image_urls && product.image_urls.length > 0) {
      setSelectedImage(product.image_urls[0]);
    } else {
      setSelectedImage(null);
    }
  };

  const handleGenerateMessage = async () => {
    if (!selectedProduct) {
      alert("Please select a product first!");
      return;
    }

    try {
      setIsGenerating(true);
      const res = await whatsappAPI.generateMessage({
        product_id: selectedProduct,
        user_prompt: prompt
      });
      
      if (res.success) {
        setGeneratedMessage(res.message);
        setIsCopied(false); // Reset copy state when new message generated
      } else {
        alert(`Failed to generate message: ${res.error}`);
      }
    } catch (e: any) {
      console.error('Generate message error:', e);
      alert(`Error: ${e.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopyMessage = () => {
    // Copy generated message to the campaign message textarea
    setPrompt(generatedMessage);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000); // Reset after 2 seconds
  };

  const handleLocalImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select a valid image file');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert('Image size should be less than 5MB');
      return;
    }

    try {
      setUploadingImage(true);
      
      // Upload to media library
      const uploadedMedia = await mediaAPI.uploadMedia({
        file: file,
        media_type: 'image',
        title: file.name,
        description: 'Campaign image upload'
      });
      
      // Set the uploaded image as selected
      setSelectedImage(uploadedMedia.public_url ?? null);
      setLocalImageFile(file);
      
      // Refresh media list
      await loadMedia();
      
      alert('✅ Image uploaded successfully!');
    } catch (err: any) {
      console.error('Upload error:', err);
      alert(`Failed to upload image: ${err.message}`);
    } finally {
      setUploadingImage(false);
    }
  };

  const handleSendMessage = async () => {
    if (!selectedProduct) {
      alert("Please select a product!");
      return;
    }
    if (!selectedImage) {
      alert("Please select an image!");
      return;
    }
    
    const messageToSend = generatedMessage || prompt.trim();
    if (!messageToSend) {
      alert("Please enter or generate a campaign message!");
      return;
    }

    try {
      setIsSending(true);
      const res = await whatsappAPI.sendCampaign({
        prompt: messageToSend,
        product_id: selectedProduct,
        image_url: selectedImage
      });
      
      if (res.success) {
        setSentResult({
          notified_count: res.notified_count,
          status: res.status,
          message: res.message
        });
        alert(`✅ Campaign sent to ${res.notified_count} users!`);
      } else {
        alert(`Failed to send campaign: ${res.error}`);
      }
    } catch (e: any) {
      console.error('Send campaign error:', e);
      alert(`Error: ${e.message}`);
    } finally {
      setIsSending(false);
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
          onClick={() => setCurrentPage("home")}
        >
          <House />
        </button>
        <div className="text-md font-bold ml-3">Run a Message Campaign</div>
      </div>

      <div className="flex flex-col gap-4 mt-4 px-4 mb-10">
        {/* Product Selection */}
        <div>
          <Label>Select Product *</Label>
          <Select onValueChange={handleProductSelect} value={selectedProduct}>
            <SelectTrigger className="mt-1">
              <SelectValue placeholder={loading ? "Loading products..." : "Choose a product"} />
            </SelectTrigger>
            <SelectContent>
              {products.map((product) => (
                <SelectItem key={product.id} value={product.id}>
                  {product.name} {product.price ? `- ₹${product.price}` : ''}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Campaign Message */}
        <div>
          <Label>Campaign Message (Optional - can be generated by AI)</Label>
          <Textarea
            placeholder="E.g., '15% discount on pots for first 100 users'"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="mt-1"
            rows={3}
          />
          <p className="text-xs text-gray-500 mt-1">Enter a hint for AI or leave blank for auto-generation</p>
        </div>

        {/* Generate Message Button */}
        <div>
          <Button
            onClick={handleGenerateMessage}
            disabled={!selectedProduct || isGenerating}
            className="w-full"
            variant="outline"
          >
            {isGenerating ? (
              <>
                <span className="animate-spin mr-2">⏳</span>
                Generating...
              </>
            ) : (
              '✨ Generate AI Message'
            )}
          </Button>
        </div>

        {/* Generated Message Preview */}
        {generatedMessage && (
          <div className="border-2 border-green-500 rounded-lg p-4 bg-green-50">
            <div className="flex justify-between items-center mb-2">
              <Label className="text-green-700 font-semibold">Generated Campaign Message:</Label>
              <Button
                onClick={handleCopyMessage}
                size="sm"
                variant="ghost"
                className="h-8 text-green-700 hover:bg-green-100"
              >
                {isCopied ? (
                  <>
                    <Check className="h-4 w-4 mr-1" />
                    Copied!
                  </>
                ) : (
                  <>
                    <svg 
                      xmlns="http://www.w3.org/2000/svg" 
                      className="h-4 w-4 mr-1" 
                      fill="none" 
                      viewBox="0 0 24 24" 
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    Copy
                  </>
                )}
              </Button>
            </div>
            <Textarea
              value={generatedMessage}
              onChange={(e) => setGeneratedMessage(e.target.value)}
              className="mt-1 bg-white"
              rows={4}
            />
            <p className="text-xs text-green-600 mt-1">✅ You can edit this message before sending</p>
          </div>
        )}

        {/* Image Selection */}
        <div>
          <div className="flex justify-between items-center">
            <Label>Select Campaign Image *</Label>
            <label htmlFor="local-image-upload">
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={uploadingImage}
                asChild
              >
                <span className="cursor-pointer">
                  {uploadingImage ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4 mr-1" />
                      Upload Local
                    </>
                  )}
                </span>
              </Button>
            </label>
            <input
              id="local-image-upload"
              type="file"
              accept="image/*"
              onChange={handleLocalImageUpload}
              className="hidden"
            />
          </div>
          
          {/* Product Images */}
          {selectedProductData?.image_urls && selectedProductData.image_urls.length > 0 && (
            <div className="mt-2">
              <p className="text-xs text-gray-600 mb-1">Product Images:</p>
              <div className="grid grid-cols-3 gap-2">
                {selectedProductData.image_urls.map((imgUrl: string, idx: number) => (
                  <div
                    key={idx}
                    onClick={() => setSelectedImage(imgUrl)}
                    className={`cursor-pointer rounded-md border-2 overflow-hidden ${
                      selectedImage === imgUrl ? 'border-blue-500' : 'border-gray-300'
                    }`}
                  >
                    <img src={imgUrl} alt={`Product ${idx + 1}`} className="h-20 w-full object-cover" />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Gallery Images */}
          <div className="mt-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowImageSelector(!showImageSelector)}
              className="w-full"
            >
              {showImageSelector ? 'Hide' : 'Show'} Gallery Images ({availableImages.length})
            </Button>
          </div>

          {showImageSelector && (
            <div className="mt-2 bg-gray-50 p-2 rounded-md max-h-60 overflow-y-auto">
              <div className="grid grid-cols-3 gap-2">
                {availableImages.map((img) => (
                  <div
                    key={img.id}
                    onClick={() => {
                      setSelectedImage(img.public_url);
                      setShowImageSelector(false);
                    }}
                    className={`cursor-pointer rounded-md border-2 overflow-hidden ${
                      selectedImage === img.public_url ? 'border-blue-500' : 'border-gray-300'
                    }`}
                  >
                    <img src={img.public_url} alt={img.title} className="h-20 w-full object-cover" />
                    <p className="text-xs p-1 truncate">{img.title}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Selected Image Preview */}
          {selectedImage && (
            <div className="mt-3 bg-white border rounded-md p-2">
              <Label className="text-xs text-gray-600">Selected Image:</Label>
              <img
                src={selectedImage}
                alt="Selected"
                className="h-32 w-full mt-1 rounded-md object-contain border"
              />
            </div>
          )}
        </div>

        {/* Send Campaign Button */}
        <Button
          className="mt-4 bg-green-600 hover:bg-green-700 text-white flex gap-2 justify-center items-center h-12"
          onClick={handleSendMessage}
          disabled={isSending || !selectedProduct || !selectedImage || !prompt.trim()}
        >
          {isSending ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              Sending Campaign...
            </>
          ) : (
            <>
              <img src="WhatsApp.webp" className="h-6 w-6" />
              Send WhatsApp Campaign
            </>
          )}
        </Button>

        {/* Success Result */}
        {sentResult && (
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <Label className="text-blue-800 text-lg">✅ Campaign Sent Successfully!</Label>
            <div className="flex justify-between items-center mt-3">
              <span className="text-sm font-medium">Users Notified:</span>
              <span className="font-bold text-xl text-blue-600">{sentResult.notified_count}</span>
            </div>
            <div className="flex justify-between items-center mt-1">
              <span className="text-sm font-medium">Status:</span>
              <span className="font-semibold text-green-600 uppercase">{sentResult.status}</span>
            </div>
            {sentResult.message && (
              <div className="mt-3 pt-3 border-t border-blue-200">
                <p className="text-xs text-gray-600 mb-1">Message sent:</p>
                <p className="text-sm text-gray-800 whitespace-pre-wrap">{sentResult.message}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

import { Checkbox } from "@/components/ui/checkbox";


const AddListing = () => {
  const { setCurrentPage } = usePage();

  // Local states
  const [selectedProduct, setSelectedProduct] = useState("");
  const [variants, setVariants] = useState<string[]>([]);
  const [platform, setPlatform] = useState("");

  // Example product data
  const products = ["Clay Pot", "Handmade Vase", "Bamboo Lamp", "Copper Bottle"];

  // Example variants
  const variantOptions = [
    { label: "Small (₹250)", value: "small" },
    { label: "Medium (₹350)", value: "medium" },
    { label: "Large (₹450)", value: "large" },
  ];

  const toggleVariant = (value: string) => {
    setVariants((prev) =>
      prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value]
    );
  };

  const handleListProduct = () => {
    if (!selectedProduct || !platform) {
      alert("Please select a product and a platform.");
      return;
    }

    console.log("📦 Listing Details:", {
      product: selectedProduct,
      variants,
      platform,
    });

    alert(`✅ ${selectedProduct} listed on ${platform}!`);
  };

  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
      style={{ backgroundImage: "url('/white_bg.png')" }}
    >
      {/* Header */}
      <div className="w-full mt-10 flex justify-between items-center p-3 border-b">
        <button
          className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white"
          onClick={() => setCurrentPage("list-products")}
        >
          <Undo2 />
        </button>
        <div className="flex w-full justify-center">
        <div className="text-md font-bold ml-3">List a Product</div>
        </div>
      </div>

      {/* Product selection */}
      <div className="px-4 mt-4">
        <Label>Choose a product to list</Label>
        <Select onValueChange={setSelectedProduct}>
          <SelectTrigger className="mt-2">
            <SelectValue placeholder="Select product" />
          </SelectTrigger>
          <SelectContent>
            {products.map((product) => (
              <SelectItem key={product} value={product}>
                {product}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Variants */}
      {/* Variants */}
      <div className="px-4 mt-5">
        <Label>Choose variants / sizes</Label>
        <div className="flex flex-col gap-2 mt-2">
          {variantOptions.map((opt) => (
            <div key={opt.value} className="flex items-center space-x-2">
              <Checkbox
                checked={variants.includes(opt.value)}
                onCheckedChange={(checked) => {
                  if (checked) {
                    setVariants((prev) => [...prev, opt.value]);
                  } else {
                    setVariants((prev) => prev.filter((v) => v !== opt.value));
                  }
                }}
                id={opt.value}
              />
              <Label htmlFor={opt.value}>{opt.label}</Label>
            </div>
          ))}
        </div>
      </div>


      {/* Platform */}
      <div className="px-4 flex flex-col justify-center gap-1 mt-5">
        <Label>Choose platform</Label>
        <div className="flex justify-center gap-2 mt-2">
          {["Amazon", "Meesho", "WhatsApp"].map((p) => (
            <Button
              key={p}
              variant={platform === p ? "default" : "outline"}
              className="w-1/3 mt-1"
              onClick={() => setPlatform(p)}
            >
              {p}
            </Button>
          ))}
        </div>
      </div>

      <Button className="mx-4 mt-6 mb-10" onClick={handleListProduct}>
        List my product
      </Button>
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
  const [availableImages, setAvailableImages] = useState<{ id: string; title: string; public_url: string }[]>([]);
  const [availableVideos, setAvailableVideos] = useState<{ id: string; title: string; public_url: string }[]>([]);
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
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: boolean }>({});

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
    const newProgress: { [key: string]: boolean } = {};

    try {
      const uploadedUrls: string[] = [];

      for (const file of uploadingFiles) {
        newProgress[file.name] = false;
        setUploadProgress({ ...newProgress });

        const response = await mediaAPI.uploadMedia({
          file,
          media_type: currentMediaType,
          title: file.name
        });

        if (response.success && response.public_url) {
          uploadedUrls.push(response.public_url);
        }

        newProgress[file.name] = true;
        setUploadProgress({ ...newProgress });
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


