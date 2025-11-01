import { useState, useEffect } from 'react';
import { usePage } from '@/contexts/PageContext';
import { Button } from '@/components/ui/button';
import { ChevronLeft, Star, ShoppingBag, Heart, Truck, RotateCcw } from 'lucide-react';

interface MyntraProduct {
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

const MyntraListing = () => {
  const { setCurrentPage, selectedProductId } = usePage();
  const [product, setProduct] = useState<MyntraProduct | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedImage, setSelectedImage] = useState(0);
  const [selectedSize, setSelectedSize] = useState('');

  useEffect(() => {
    loadMyntraListing();
  }, [selectedProductId]);

  const loadMyntraListing = async () => {
    console.log('🔵 [MyntraListing] Loading listing...');
    console.log('   Product ID:', selectedProductId);
    
    try {
      setLoading(true);
      const apiUrl = `https://backend-557742533869.asia-south1.run.app/api/marketplace/${selectedProductId}/myntra-listing`;
      
      console.log('🚀 [MyntraListing] Calling API...');
      console.log('   URL:', apiUrl);
      
      const response = await fetch(apiUrl, {
        credentials: 'include'
      });
      
      console.log('📡 [MyntraListing] Response received');
      console.log('   Status:', response.status);
      console.log('   OK:', response.ok);
      
      const data = await response.json();
      console.log('📄 [MyntraListing] Response data:', JSON.stringify(data, null, 2));
      
      if (data.success) {
        console.log('✅ [MyntraListing] Listing loaded successfully');
        setProduct(data.listing);
      } else {
        console.error('❌ [MyntraListing] API returned failure:', data);
      }
    } catch (error) {
      console.error('❌ [MyntraListing] Error loading listing:', error);
    } finally {
      setLoading(false);
      console.log('🏁 [MyntraListing] Load completed');
    }
  };

  const handleBack = () => {
    setCurrentPage('marketplace-listings');
  };

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Myntra listing...</p>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-white p-4">
        <div className="text-center">
          <p className="text-gray-600">Product not found on Myntra</p>
          <Button onClick={handleBack} className="mt-4">Go Back</Button>
        </div>
      </div>
    );
  }

  const discount = product.original_price && product.original_price > product.price
    ? Math.round(((product.original_price - product.price) / product.original_price) * 100)
    : 0;

  const sizes = ['S', 'M', 'L', 'XL']; // Default sizes for demo

  return (
    <div className="w-full h-full flex flex-col bg-white">
      {/* Myntra-style Header */}
      <div className="flex-shrink-0 bg-white border-b shadow-sm">
        <div className="px-4 py-3 flex items-center justify-between">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={handleBack}
            className="p-1 hover:bg-gray-100"
          >
            <ChevronLeft className="h-6 w-6 text-gray-700" />
          </Button>
          <div className="flex-1 text-center">
            <span className="font-bold text-xl" style={{ fontFamily: 'Assistant, sans-serif' }}>
              <span className="text-pink-500">M</span>
              <span className="text-gray-800">YNTRA</span>
            </span>
          </div>
          <div className="flex gap-4">
            <Heart className="h-5 w-5 text-gray-700" />
            <ShoppingBag className="h-5 w-5 text-gray-700" />
          </div>
        </div>
      </div>

      {/* Content - Scrollable */}
      <div className="flex-1 overflow-y-auto pb-24">
        {/* Product Images */}
        <div className="bg-white">
          <div className="relative">
            <img 
              src={product.images[selectedImage] || '/placeholder.png'} 
              alt={product.title}
              className="w-full h-96 object-contain bg-gray-50"
            />
            
            {/* Image counter */}
            <div className="absolute bottom-4 right-4 bg-white/80 backdrop-blur-sm rounded-full px-3 py-1 text-xs">
              {selectedImage + 1}/{product.images.length}
            </div>
          </div>
          
          {product.images.length > 1 && (
            <div className="flex gap-2 p-3 overflow-x-auto">
              {product.images.map((img, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedImage(idx)}
                  className={`flex-shrink-0 w-16 h-16 border rounded ${
                    selectedImage === idx ? 'border-pink-500 border-2' : 'border-gray-200'
                  }`}
                >
                  <img src={img} alt={`View ${idx + 1}`} className="w-full h-full object-cover rounded" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Product Info */}
        <div className="px-4 py-3 border-b">
          <div className="text-xl font-bold text-gray-800 mb-1">{product.seller}</div>
          <h1 className="text-sm text-gray-600 leading-tight mb-3">{product.title}</h1>
          
          {/* Rating & Reviews */}
          <div className="flex items-center gap-2 pb-3 border-b">
            <div className="flex items-center gap-1 border border-gray-300 rounded px-2 py-1">
              <span className="text-sm font-semibold">{product.rating}</span>
              <Star className="h-3 w-3 fill-green-600 text-green-600" />
            </div>
            <span className="text-sm text-gray-600">
              {product.reviews_count.toLocaleString()} Ratings
            </span>
          </div>
        </div>

        {/* Price Section */}
        <div className="px-4 py-4 border-b">
          <div className="flex items-baseline gap-2 mb-3">
            <span className="text-2xl font-bold">₹{product.price.toLocaleString()}</span>
            {product.original_price && discount > 0 && (
              <>
                <span className="text-base text-gray-400 line-through">₹{product.original_price.toLocaleString()}</span>
                <span className="text-base text-orange-500 font-semibold">({discount}% OFF)</span>
              </>
            )}
          </div>
          <div className="text-xs text-green-600 font-semibold">inclusive of all taxes</div>
        </div>

        {/* Size Selection (Generic for demo) */}
        <div className="px-4 py-4 border-b">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-semibold">SELECT SIZE</span>
            <button className="text-xs text-pink-500 font-semibold">SIZE CHART →</button>
          </div>
          <div className="flex gap-3">
            {sizes.map((size) => (
              <button
                key={size}
                onClick={() => setSelectedSize(size)}
                className={`w-14 h-10 border rounded-full text-sm font-semibold ${
                  selectedSize === size
                    ? 'border-pink-500 text-pink-500'
                    : 'border-gray-300 text-gray-700 hover:border-pink-300'
                }`}
              >
                {size}
              </button>
            ))}
          </div>
        </div>

        {/* Delivery & Services */}
        <div className="px-4 py-4 border-b">
          <div className="text-sm font-semibold mb-3">DELIVERY OPTIONS</div>
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <Truck className="h-5 w-5 text-gray-600" />
              <div className="text-sm">
                <div className="font-medium">Express Delivery</div>
                <div className="text-gray-600 text-xs">{product.delivery_date || 'Get it by tomorrow'}</div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <RotateCcw className="h-5 w-5 text-gray-600" />
              <div className="text-sm">
                <div className="font-medium">Easy 14 days return & exchange</div>
                <div className="text-gray-600 text-xs">Choose to return or exchange for a different size</div>
              </div>
            </div>
          </div>
        </div>

        {/* Product Details */}
        {product.bullets && product.bullets.length > 0 && (
          <div className="px-4 py-4 border-b">
            <div className="text-sm font-semibold mb-3">PRODUCT DETAILS</div>
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

        {/* Description */}
        <div className="px-4 py-4 border-b">
          <div className="text-sm font-semibold mb-3">PRODUCT DESCRIPTION</div>
          <p className="text-sm text-gray-700 whitespace-pre-line leading-relaxed">{product.description}</p>
        </div>

        {/* Specifications */}
        {Object.keys(product.specifications).length > 0 && (
          <div className="px-4 py-4 border-b">
            <div className="text-sm font-semibold mb-3">SPECIFICATIONS</div>
            <div className="space-y-2">
              {Object.entries(product.specifications).map(([key, value]) => (
                <div key={key} className="flex text-sm">
                  <div className="w-1/3 text-gray-500">{key}</div>
                  <div className="w-2/3 text-gray-900">{value}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Seller */}
        <div className="px-4 py-4 border-b">
          <div className="text-sm font-semibold mb-2">Sold by: {product.seller}</div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 bg-green-600 text-white px-2 py-0.5 rounded text-xs">
              <span>4.3</span>
              <Star className="h-2.5 w-2.5 fill-white" />
            </div>
            <span className="text-xs text-gray-600">Seller Rating</span>
          </div>
        </div>
      </div>

      {/* Bottom Action Bar - Fixed */}
      <div className="flex-shrink-0 bg-white border-t shadow-2xl">
        <div className="px-4 py-3 flex gap-3">
          <Button 
            className="flex-1 bg-white hover:bg-gray-50 text-gray-900 border border-gray-300 font-semibold text-base py-6"
            onClick={() => alert('Add to Wishlist functionality would go here')}
          >
            <Heart className="h-5 w-5 mr-2" />
            WISHLIST
          </Button>
          <Button 
            className="flex-1 bg-pink-500 hover:bg-pink-600 text-white font-semibold text-base py-6"
            onClick={() => alert('Add to Bag functionality would go here')}
          >
            <ShoppingBag className="h-5 w-5 mr-2" />
            ADD TO BAG
          </Button>
        </div>
      </div>
    </div>
  );
};

export default MyntraListing;
