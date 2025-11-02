import { useState, useEffect } from 'react';
import { usePage } from '@/contexts/PageContext';
import { Button } from '@/components/ui/button';
import { ChevronLeft, Star, ShoppingCart, Heart, Share2, Zap, TrendingUp } from 'lucide-react';

interface FlipkartProduct {
  product_id: string;
  title: string;
  description: string;
  price: number;
  original_price?: number;
  rating: number;
  reviews_count: number;
  bullets: string[];
  specifications: { [key: string]: string };
  images: string[];
  in_stock: boolean;
  delivery_date?: string;
  seller: string;
}

const FlipkartListing = () => {
  const { setCurrentPage, selectedProductId } = usePage();
  const [product, setProduct] = useState<FlipkartProduct | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedImage, setSelectedImage] = useState(0);

  useEffect(() => {
    loadFlipkartListing();
  }, [selectedProductId]);

  const loadFlipkartListing = async () => {
    console.log('🔵 [FlipkartListing] Loading listing...');
    console.log('   Product ID:', selectedProductId);
    
    try {
      setLoading(true);
      //const apiUrl = `https://backend-557742533869.asia-south1.run.app/api/marketplace/${selectedProductId}/flipkart-listing`;
      const apiUrl = `/api/marketplace/${selectedProductId}/flipkart-listing`;
      
      console.log('🚀 [FlipkartListing] Calling API...');
      console.log('   URL:', apiUrl);
      
      const response = await fetch(apiUrl, {
        credentials: 'include'
      });
      
      console.log('📡 [FlipkartListing] Response received');
      console.log('   Status:', response.status);
      console.log('   OK:', response.ok);
      
      const data = await response.json();
      console.log('📄 [FlipkartListing] Response data:', JSON.stringify(data, null, 2));
      
      if (data.success) {
        console.log('✅ [FlipkartListing] Listing loaded successfully');
        setProduct(data.listing);
      } else {
        console.error('❌ [FlipkartListing] API returned failure:', data);
      }
    } catch (error) {
      console.error('❌ [FlipkartListing] Error loading listing:', error);
    } finally {
      setLoading(false);
      console.log('🏁 [FlipkartListing] Load completed');
    }
  };

  const handleBack = () => {
    setCurrentPage('marketplace-listings');
  };

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Flipkart listing...</p>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-white p-4">
        <div className="text-center">
          <p className="text-gray-600">Product not found on Flipkart</p>
          <Button onClick={handleBack} className="mt-4">Go Back</Button>
        </div>
      </div>
    );
  }

  const discount = product.original_price && product.original_price > product.price
    ? Math.round(((product.original_price - product.price) / product.original_price) * 100)
    : 0;

  return (
    <div className="w-full h-full flex flex-col bg-white">
      {/* Flipkart-style Header */}
      <div className="flex-shrink-0 bg-[#2874F0] text-white shadow-md">
        <div className="px-4 py-3 flex items-center justify-between">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={handleBack}
            className="text-white hover:bg-[#1C5BBF] p-1"
          >
            <ChevronLeft className="h-6 w-6" />
          </Button>
          <div className="flex-1 text-center">
            <span className="font-bold text-lg italic">Flipkart</span>
          </div>
          <div className="flex gap-3">
            <ShoppingCart className="h-5 w-5" />
          </div>
        </div>
      </div>

      {/* Content - Scrollable */}
      <div className="flex-1 overflow-y-auto pb-20">
        {/* Product Images */}
        <div className="bg-white p-4">
          <div className="relative bg-gray-50 rounded-lg">
            <img 
              src={product.images[selectedImage] || '/placeholder.png'} 
              alt={product.title}
              className="w-full h-80 object-contain"
            />
            
            {/* Wishlist & Share buttons on image */}
            <div className="absolute top-3 right-3 flex gap-2">
              <button className="bg-white rounded-full p-2 shadow-md">
                <Heart className="h-5 w-5 text-gray-600" />
              </button>
              <button className="bg-white rounded-full p-2 shadow-md">
                <Share2 className="h-5 w-5 text-gray-600" />
              </button>
            </div>
          </div>
          
          {product.images.length > 1 && (
            <div className="flex gap-2 mt-3 overflow-x-auto">
              {product.images.map((img, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedImage(idx)}
                  className={`flex-shrink-0 w-16 h-16 border-2 rounded ${
                    selectedImage === idx ? 'border-blue-500' : 'border-gray-200'
                  }`}
                >
                  <img src={img} alt={`View ${idx + 1}`} className="w-full h-full object-cover rounded" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Product Title */}
        <div className="px-4 py-3 border-b-8 border-gray-100">
          <h1 className="text-base font-medium leading-tight mb-2">{product.title}</h1>
          
          {/* Rating & Reviews */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1 bg-green-600 text-white px-2 py-1 rounded text-xs">
              <span className="font-semibold">{product.rating}</span>
              <Star className="h-3 w-3 fill-white" />
            </div>
            <span className="text-sm text-gray-600">
              {product.reviews_count.toLocaleString()} Ratings & Reviews
            </span>
          </div>
        </div>

        {/* Price Section */}
        <div className="px-4 py-4 border-b-8 border-gray-100">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-3xl font-medium">₹{product.price.toLocaleString()}</span>
            {product.original_price && discount > 0 && (
              <>
                <span className="text-lg text-gray-500 line-through">₹{product.original_price.toLocaleString()}</span>
                <span className="text-lg text-green-600 font-medium">{discount}% off</span>
              </>
            )}
          </div>
          
          {/* Offers */}
          <div className="bg-yellow-50 border border-yellow-200 rounded p-2 mt-3">
            <div className="flex items-center gap-2 text-sm font-medium mb-1">
              <TrendingUp className="h-4 w-4 text-green-600" />
              <span>Available offers</span>
            </div>
            <div className="text-xs text-gray-700 space-y-1">
              <div>• Bank Offer: 10% off on HDFC Bank Credit Card</div>
              <div>• Special Price: Get extra 5% off (price inclusive of discount)</div>
            </div>
          </div>

          {/* Delivery */}
          {product.delivery_date && (
            <div className="mt-3 pt-3 border-t">
              <div className="text-sm text-gray-700">
                <span className="font-medium">Delivery by </span>
                <span className="font-semibold">{product.delivery_date}</span>
                <span> | </span>
                <span className="text-green-600 font-medium">Free</span>
              </div>
            </div>
          )}
        </div>

        {/* Highlights */}
        {product.bullets && product.bullets.length > 0 && (
          <div className="px-4 py-4 border-b-8 border-gray-100">
            <h2 className="font-medium text-base mb-3">Highlights</h2>
            <ul className="space-y-2">
              {product.bullets.map((bullet, idx) => (
                <li key={idx} className="text-sm text-gray-700 flex gap-2">
                  <span className="text-gray-400">•</span>
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Seller */}
        <div className="px-4 py-4 border-b-8 border-gray-100">
          <div className="flex justify-between items-center">
            <div>
              <div className="text-xs text-gray-500">Sold by</div>
              <div className="text-sm font-medium text-blue-600">{product.seller}</div>
            </div>
            <div className="flex items-center gap-1 bg-blue-600 text-white px-3 py-1 rounded text-xs">
              <span className="font-semibold">4.2</span>
              <Star className="h-3 w-3 fill-white" />
            </div>
          </div>
        </div>

        {/* Product Description */}
        <div className="px-4 py-4 border-b-8 border-gray-100">
          <h2 className="font-medium text-base mb-3">Product Description</h2>
          <p className="text-sm text-gray-700 whitespace-pre-line leading-relaxed">{product.description}</p>
        </div>

        {/* Specifications */}
        {Object.keys(product.specifications).length > 0 && (
          <div className="px-4 py-4 border-b-8 border-gray-100">
            <h2 className="font-medium text-base mb-3">Specifications</h2>
            <div className="space-y-1">
              {Object.entries(product.specifications).map(([key, value], idx) => (
                <div 
                  key={key} 
                  className={`flex py-3 ${idx !== 0 ? 'border-t' : ''}`}
                >
                  <div className="w-1/3 text-sm text-gray-500">{key}</div>
                  <div className="w-2/3 text-sm text-gray-900 font-medium">{value}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Bottom Action Bar - Fixed */}
      <div className="flex-shrink-0 bg-white border-t shadow-2xl">
        <div className="px-4 py-3 flex gap-3">
          <Button 
            className="flex-1 bg-[#FF9F00] hover:bg-[#E68E00] text-white font-semibold text-base py-6"
            onClick={() => alert('Add to Cart functionality would go here')}
          >
            <ShoppingCart className="h-5 w-5 mr-2" />
            ADD TO CART
          </Button>
          <Button 
            className="flex-1 bg-[#FB641B] hover:bg-[#E05A19] text-white font-semibold text-base py-6"
            onClick={() => alert('Buy Now functionality would go here')}
          >
            <Zap className="h-5 w-5 mr-2" />
            BUY NOW
          </Button>
        </div>
      </div>
    </div>
  );
};

export default FlipkartListing;
