import { useState, useEffect } from 'react';
import { usePage } from '@/contexts/PageContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { House, ExternalLink, Eye, Loader2 } from 'lucide-react';

interface MarketplaceListing {
  id: string;
  product_id: string;
  product_name: string;
  marketplace: string;
  status: 'active' | 'pending' | 'draft';
  listed_at: string;
  image_url: string;
  price: number;
  views?: number;
}

const MarketplaceListings = () => {
  const { setCurrentPage, setSelectedProductId } = usePage();
  const [listings, setListings] = useState<MarketplaceListing[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadListings();
  }, []);

  const loadListings = async () => {
    console.log('🔵 [MarketplaceListings] Loading listings...');
    
    try {
      setLoading(true);
      const apiUrl = 'https://backend-557742533869.asia-south1.run.app/api/marketplace/listings';
      //const apiUrl = '/api/marketplace/listings';
      
      console.log('🚀 [MarketplaceListings] Calling API...');
      console.log('   URL:', apiUrl);
      
      const response = await fetch(apiUrl, {
        credentials: 'include'
      });
      
      console.log('📡 [MarketplaceListings] Response received');
      console.log('   Status:', response.status);
      console.log('   OK:', response.ok);
      
      const data = await response.json();
      console.log('📄 [MarketplaceListings] Response data:', JSON.stringify(data, null, 2));
      
      if (data.success) {
        console.log(`✅ [MarketplaceListings] Loaded ${data.listings.length} listings`);
        setListings(data.listings);
      } else {
        console.error('❌ [MarketplaceListings] API returned failure:', data);
      }
    } catch (error) {
      console.error('❌ [MarketplaceListings] Error loading listings:', error);
    } finally {
      setLoading(false);
      console.log('🏁 [MarketplaceListings] Load completed');
    }
  };

  const handleViewListing = (listing: MarketplaceListing) => {
    setSelectedProductId(listing.product_id);
    
    // Route to appropriate marketplace view
    if (listing.marketplace === 'amazon') {
      setCurrentPage('amazon-listing');
    } else if (listing.marketplace === 'flipkart') {
      setCurrentPage('flipkart-listing');
    } else if (listing.marketplace === 'myntra') {
      setCurrentPage('myntra-listing');
    }
  };

  const getMarketplaceLogo = (marketplace: string) => {
    const logos: { [key: string]: string } = {
      amazon: '/amazon_logo.png',
      flipkart: '/flipkart_logo.png',
      myntra: '/myntra_logo.png',
    };
    return logos[marketplace] || '/placeholder.png';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'draft':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="w-full h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="flex-shrink-0 bg-white border-b shadow-sm">
        <div className="px-4 py-3 flex items-center justify-between">
          <button
            className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white"
            onClick={() => setCurrentPage('home')}
          >
            <House />
          </button>
          <h1 className="font-semibold text-lg">Marketplace Listings</h1>
          <div className="w-10"></div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <div className="text-center">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-3" />
              <p className="text-gray-600">Loading your listings...</p>
            </div>
          </div>
        ) : listings.length === 0 ? (
          <Card>
            <CardContent className="pt-6 text-center py-12">
              <ExternalLink className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h2 className="text-xl font-semibold mb-2">No Marketplace Listings</h2>
              <p className="text-gray-600 mb-4">
                You haven't listed any products on marketplaces yet.
              </p>
              <Button onClick={() => setCurrentPage('list-products')}>
                Go to Products
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {listings.map((listing) => (
              <Card key={listing.id} className="overflow-hidden">
                <CardContent className="p-0">
                  <div className="flex gap-3 p-3">
                    {/* Product Image */}
                    <div className="flex-shrink-0">
                      <img 
                        src={listing.image_url || '/placeholder.png'} 
                        alt={listing.product_name}
                        className="w-20 h-20 object-cover rounded-lg"
                      />
                    </div>

                    {/* Listing Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <h3 className="font-medium text-sm line-clamp-2">{listing.product_name}</h3>
                        <Badge className={getStatusColor(listing.status)}>
                          {listing.status}
                        </Badge>
                      </div>

                      {/* Marketplace Logo */}
                      <div className="flex items-center gap-2 mb-2">
                        <img 
                          src={getMarketplaceLogo(listing.marketplace)} 
                          alt={listing.marketplace}
                          className="h-4 object-contain"
                          onError={(e) => {
                            e.currentTarget.style.display = 'none';
                          }}
                        />
                        <span className="text-xs text-gray-600 capitalize">{listing.marketplace}</span>
                      </div>

                      {/* Price & Stats */}
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="text-sm font-semibold text-green-700">₹{listing.price.toLocaleString()}</span>
                        </div>
                        {listing.views !== undefined && (
                          <div className="flex items-center gap-1 text-xs text-gray-500">
                            <Eye className="h-3 w-3" />
                            <span>{listing.views}</span>
                          </div>
                        )}
                      </div>

                      {/* Listed Date */}
                      <div className="text-xs text-gray-500 mt-1">
                        Listed on {new Date(listing.listed_at).toLocaleDateString('en-IN', {
                          day: 'numeric',
                          month: 'short',
                          year: 'numeric'
                        })}
                      </div>

                      {/* Action Button */}
                      <Button 
                        size="sm" 
                        variant="outline" 
                        className="w-full mt-2"
                        onClick={() => handleViewListing(listing)}
                      >
                        <ExternalLink className="h-3 w-3 mr-1" />
                        View on {listing.marketplace.charAt(0).toUpperCase() + listing.marketplace.slice(1)}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MarketplaceListings;
