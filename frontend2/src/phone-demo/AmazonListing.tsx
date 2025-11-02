import { useState, useEffect } from 'react';
import { usePage } from '@/contexts/PageContext';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ChevronLeft, Star, ShoppingCart, Heart, Share2, ChevronRight } from 'lucide-react';

interface AmazonProduct {
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

const AmazonListing = () => {
  const { setCurrentPage, selectedProductId } = usePage();
  const [product, setProduct] = useState<AmazonProduct | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedImage, setSelectedImage] = useState(0);
  const [quantity, setQuantity] = useState(1);

  useEffect(() => {
    loadAmazonListing();
  }, [selectedProductId]);

  const loadAmazonListing = async () => {
    console.log('🔵 [AmazonListing] Loading listing...');
    console.log('   Product ID:', selectedProductId);
    
    try {
      setLoading(true);
      //const apiUrl = `https://backend-557742533869.asia-south1.run.app/api/marketplace/${selectedProductId}/amazon-listing`;
      const apiUrl = `/api/marketplace/${selectedProductId}/amazon-listing`;
      
      console.log('🚀 [AmazonListing] Calling API...');
      console.log('   URL:', apiUrl);
      
      // Fetch Amazon listing data from backend
      const response = await fetch(apiUrl, {
        credentials: 'include'
      });
      
      console.log('📡 [AmazonListing] Response received');
      console.log('   Status:', response.status);
      console.log('   OK:', response.ok);
      
      const data = await response.json();
      console.log('📄 [AmazonListing] Response data:', JSON.stringify(data, null, 2));
      
      if (data.success) {
        console.log('✅ [AmazonListing] Listing loaded successfully');
        setProduct(data.listing);
      } else {
        console.error('❌ [AmazonListing] API returned failure:', data);
      }
    } catch (error) {
      console.error('❌ [AmazonListing] Error loading listing:', error);
    } finally {
      setLoading(false);
      console.log('🏁 [AmazonListing] Load completed');
    }
  };

  const handleBack = () => {
    setCurrentPage('marketplace-listings');
  };

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Amazon listing...</p>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-white p-4">
        <div className="text-center">
          <p className="text-gray-600">Product not found on Amazon</p>
          <Button onClick={handleBack} className="mt-4">Go Back</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full flex flex-col bg-white">
      {/* Amazon-style Header */}
      <div className="flex-shrink-0 bg-[#232F3E] text-white">
        <div className="px-3 py-2 flex items-center justify-between">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={handleBack}
            className="text-white hover:bg-[#374151]"
          >
            <ChevronLeft className="h-5 w-5" />
          </Button>
          <img src="/amazon-logo-white.png" alt="Amazon" className="h-6" onError={(e) => {
            e.currentTarget.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 30"><text x="10" y="20" fill="white" font-size="16" font-family="Arial">amazon.in</text></svg>';
          }} />
          <div className="flex gap-2">
            <ShoppingCart className="h-5 w-5" />
          </div>
        </div>
        
        {/* Search bar */}
        <div className="px-3 pb-2">
          <div className="bg-white rounded flex items-center px-3 py-1">
            <input 
              type="text" 
              placeholder="Search Amazon.in" 
              className="flex-1 text-sm text-gray-700 outline-none"
              disabled
            />
          </div>
        </div>
      </div>

      {/* Content - Scrollable */}
      <div className="flex-1 overflow-y-auto pb-20">
        {/* Product Images */}
        <div className="bg-white p-3">
          <div className="relative">
            <img 
              src={product.images[selectedImage] || '/placeholder.png'} 
              alt={product.title}
              className="w-full h-64 object-contain"
            />
            {product.images.length > 1 && (
              <div className="flex justify-center gap-2 mt-3">
                {product.images.map((img, idx) => (
                  <button
                    key={idx}
                    onClick={() => setSelectedImage(idx)}
                    className={`w-12 h-12 border-2 rounded ${
                      selectedImage === idx ? 'border-orange-500' : 'border-gray-200'
                    }`}
                  >
                    <img src={img} alt={`View ${idx + 1}`} className="w-full h-full object-cover" />
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Product Title & Brand */}
        <div className="px-3 py-2 border-b">
          <div className="text-xs text-gray-600 mb-1">Visit the {product.seller} Store</div>
          <h1 className="text-base font-normal leading-tight">{product.title}</h1>
        </div>

        {/* Rating & Reviews */}
        <div className="px-3 py-2 border-b flex items-center gap-3">
          <div className="flex items-center gap-1">
            <span className="text-sm font-semibold">{product.rating}</span>
            <div className="flex">
              {[...Array(5)].map((_, i) => (
                <Star 
                  key={i}
                  className={`h-3 w-3 ${
                    i < Math.floor(product.rating) 
                      ? 'fill-orange-400 text-orange-400' 
                      : 'text-gray-300'
                  }`}
                />
              ))}
            </div>
          </div>
          <span className="text-sm text-blue-600">{product.reviews_count.toLocaleString()} ratings</span>
        </div>

        {/* Price */}
        <div className="px-3 py-3 border-b">
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-600">Price:</span>
            <span className="text-2xl text-[#B12704]">₹{product.price.toLocaleString()}</span>
          </div>
          {product.original_price && product.original_price > product.price && (
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs text-gray-600">M.R.P.:</span>
              <span className="text-xs text-gray-600 line-through">₹{product.original_price.toLocaleString()}</span>
              <span className="text-xs text-[#B12704]">
                ({Math.round(((product.original_price - product.price) / product.original_price) * 100)}% off)
              </span>
            </div>
          )}
          <div className="text-xs text-gray-600 mt-1">Inclusive of all taxes</div>
        </div>

        {/* Stock & Delivery */}
        <div className="px-3 py-3 border-b">
          <div className="text-sm">
            {product.in_stock ? (
              <span className="text-green-700 font-semibold">In Stock.</span>
            ) : (
              <span className="text-red-700 font-semibold">Currently unavailable.</span>
            )}
          </div>
          {product.delivery_date && (
            <div className="text-sm mt-2">
              <span className="text-gray-700">FREE delivery </span>
              <span className="font-semibold">{product.delivery_date}</span>
            </div>
          )}
        </div>

        {/* About this item */}
        {product.bullets && product.bullets.length > 0 && (
          <div className="px-3 py-3 border-b">
            <h2 className="font-semibold text-sm mb-2">About this item</h2>
            <ul className="space-y-1">
              {product.bullets.map((bullet, idx) => (
                <li key={idx} className="text-sm text-gray-700 flex gap-2">
                  <span>•</span>
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Product Description */}
        <div className="px-3 py-3 border-b">
          <h2 className="font-semibold text-sm mb-2">Product Description</h2>
          <p className="text-sm text-gray-700 whitespace-pre-line">{product.description}</p>
        </div>

        {/* Technical Specifications */}
        {Object.keys(product.specifications).length > 0 && (
          <div className="px-3 py-3 border-b">
            <h2 className="font-semibold text-sm mb-2">Technical Details</h2>
            <div className="space-y-2">
              {Object.entries(product.specifications).map(([key, value]) => (
                <div key={key} className="flex text-sm">
                  <div className="w-1/3 text-gray-600">{key}</div>
                  <div className="w-2/3 text-gray-900">{value}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Seller Info */}
        <div className="px-3 py-3 border-b">
          <div className="flex justify-between items-center">
            <div>
              <div className="text-xs text-gray-600">Sold by</div>
              <div className="text-sm text-blue-600">{product.seller}</div>
            </div>
            <ChevronRight className="h-4 w-4 text-gray-400" />
          </div>
        </div>
      </div>

      {/* Bottom Action Bar - Fixed */}
      <div className="flex-shrink-0 bg-white border-t shadow-lg">
        <div className="px-3 py-2">
          <div className="flex gap-2 mb-2">
            <Button 
              className="flex-1 bg-[#FFD814] hover:bg-[#F7CA00] text-gray-900 font-semibold"
              onClick={() => alert('Add to Cart functionality would go here')}
            >
              <ShoppingCart className="h-4 w-4 mr-2" />
              Add to Cart
            </Button>
            <Button 
              className="flex-1 bg-[#FFA41C] hover:bg-[#FF8F00] text-gray-900 font-semibold"
              onClick={() => alert('Buy Now functionality would go here')}
            >
              Buy Now
            </Button>
          </div>
          <div className="flex justify-center gap-6 text-xs text-gray-600">
            <button className="flex items-center gap-1">
              <Heart className="h-4 w-4" />
              <span>Wishlist</span>
            </button>
            <button className="flex items-center gap-1">
              <Share2 className="h-4 w-4" />
              <span>Share</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AmazonListing;
