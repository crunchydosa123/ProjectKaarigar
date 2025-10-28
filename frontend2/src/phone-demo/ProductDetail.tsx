import React, { useState, useEffect } from 'react';
import { usePage } from '@/contexts/PageContext';
import { ChevronLeft, Edit2, Share2, ShoppingBag, Package, Image as ImageIcon, Video, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { productAPI } from '@/lib/api';

interface Variant {
  description?: string;
  color?: string;
  size?: string;
  price?: number | string;
  stock?: number | string;
  image_url?: string;
  video_url?: string;
}

interface Product {
  id: string;
  name: string;
  description?: string;
  price?: number;
  stock?: number;
  currency?: string;
  variants?: Variant[];
  image_urls?: string[];
  video_urls?: string[];
  created_at?: string;
  updated_at?: string;
}

const ProductDetail: React.FC = () => {
  const { selectedProductId, setCurrentPage } = usePage();
  const productId = selectedProductId;
  
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showShareDialog, setShowShareDialog] = useState(false);
  const [showListDialog, setShowListDialog] = useState(false);
  
  // Edit form state
  const [editForm, setEditForm] = useState({
    name: '',
    description: '',
    price: 0,
    stock: 0,
    currency: 'INR'
  });

  // Fetch product details
  useEffect(() => {
    const fetchProduct = async () => {
      try {
        setLoading(true);
        const response = await productAPI.list();
        
        if (response.success) {
          const foundProduct = response.products.find((p: Product) => p.id === productId);
          if (foundProduct) {
            setProduct(foundProduct);
            setEditForm({
              name: foundProduct.name || '',
              description: foundProduct.description || '',
              price: foundProduct.price || 0,
              stock: foundProduct.stock || 0,
              currency: foundProduct.currency || 'INR'
            });
          } else {
            setError('Product not found');
          }
        }
      } catch (err) {
        console.error('Error fetching product:', err);
        setError('Failed to load product details');
      } finally {
        setLoading(false);
      }
    };

    if (productId) {
      fetchProduct();
    }
  }, [productId]);

  const handleBack = () => {
    setCurrentPage('list-products');
  };

  const handleEdit = () => {
    setShowEditDialog(true);
  };

  const handleSaveEdit = async () => {
    try {
      setLoading(true);
      // Call backend update route
      if (!productId) throw new Error('Missing product id');
      const payload = {
        name: editForm.name,
        description: editForm.description,
        price: editForm.price,
        stock: editForm.stock,
        currency: editForm.currency
      };

      const res = await productAPI.update(productId, payload);
      if (res && res.success) {
        // Refresh product data from server
        const listResp = await productAPI.list();
        if (listResp && listResp.success) {
          const updated = listResp.products.find((p: Product) => p.id === productId);
          if (updated) setProduct(updated);
        }
        setShowEditDialog(false);
        alert('Product updated successfully');
      } else {
        throw new Error((res && (res as any).error) || 'Update failed');
      }
    } catch (err: any) {
      console.error('Failed to update product', err);
      alert('Failed to update product: ' + (err.message || err));
    } finally {
      setLoading(false);
    }
  };

  const handleShare = (platform: string) => {
    if (!product) return;

    const productUrl = window.location.href;
    const text = `Check out ${product.name}! ${product.description || ''}`;
    
    let shareUrl = '';
    
    switch (platform) {
      case 'whatsapp':
        shareUrl = `https://wa.me/?text=${encodeURIComponent(text + ' ' + productUrl)}`;
        break;
      case 'twitter':
        shareUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(productUrl)}`;
        break;
      case 'instagram':
        alert('Please share manually on Instagram by copying the product details!');
        return;
      case 'facebook':
        shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(productUrl)}`;
        break;
    }
    
    if (shareUrl) {
      window.open(shareUrl, '_blank', 'width=600,height=400');
    }
  };

  const handleListOnMarketplace = (marketplace: string) => {
    alert(`List on ${marketplace} - Integration coming soon!\n\nThis will allow you to automatically list your product on ${marketplace} with all images, descriptions, and variants.`);
  };

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading product details...</p>
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-50 p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6 text-center">
            <Package className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Product Not Found</h2>
            <p className="text-gray-600 mb-4">{error || 'This product does not exist'}</p>
            <Button onClick={handleBack}>Go Back</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="w-full h-full flex flex-col bg-gray-50">
      {/* Header - Fixed */}
      <div className="flex-shrink-0 bg-white border-b shadow-sm">
        <div className="px-4 py-3 flex items-center justify-between">
          <Button variant="ghost" size="sm" onClick={handleBack}>
            <ChevronLeft className="h-5 w-5 mr-1" />
            Back
          </Button>
          <h1 className="font-semibold text-lg">Product Details</h1>
          <Button variant="ghost" size="sm" onClick={handleEdit}>
            <Edit2 className="h-4 w-4 mr-1" />
            Edit
          </Button>
        </div>
      </div>

      {/* Content - Scrollable */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4 space-y-4 pb-20">
        {/* Product Images Carousel */}
        {product.image_urls && product.image_urls.length > 0 && (
          <Card>
            <CardContent className="p-0">
              <div className="relative aspect-square bg-gray-100 overflow-hidden">
                <img
                  src={product.image_urls[0]}
                  alt={product.name}
                  className="w-full h-full object-cover"
                />
                {product.image_urls.length > 1 && (
                  <Badge className="absolute bottom-2 right-2 bg-black/60">
                    <ImageIcon className="h-3 w-3 mr-1" />
                    {product.image_urls.length} Images
                  </Badge>
                )}
              </div>
              {/* Thumbnail grid */}
              {product.image_urls.length > 1 && (
                <div className="grid grid-cols-4 gap-2 p-3">
                  {product.image_urls.slice(1, 5).map((url, idx) => (
                    <div key={idx} className="aspect-square bg-gray-100 rounded overflow-hidden">
                      <img src={url} alt={`Product ${idx + 2}`} className="w-full h-full object-cover" />
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Product Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">{product.name}</CardTitle>
            <div className="flex items-baseline gap-2 mt-2">
              <span className="text-3xl font-bold text-blue-600">
                {product.currency || 'INR'} {product.price || 'N/A'}
              </span>
              {product.stock !== undefined && (
                <Badge variant={product.stock > 0 ? 'default' : 'destructive'}>
                  {product.stock > 0 ? `${product.stock} in stock` : 'Out of stock'}
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {product.description && (
              <div>
                <h3 className="font-semibold mb-2">Description</h3>
                <p className="text-gray-700 whitespace-pre-wrap">{product.description}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-3">
          <Button
            onClick={() => setShowListDialog(true)}
            variant="outline"
            className="h-auto py-4 flex-col gap-2"
          >
            <ShoppingBag className="h-6 w-6" />
            <span className="text-sm">List on Marketplace</span>
          </Button>
          <Button
            onClick={() => setShowShareDialog(true)}
            variant="outline"
            className="h-auto py-4 flex-col gap-2"
          >
            <Share2 className="h-6 w-6" />
            <span className="text-sm">Share Product</span>
          </Button>
        </div>

        {/* Variants */}
        {product.variants && product.variants.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Product Variants ({product.variants.length})</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {product.variants.map((variant, idx) => (
                <div key={idx} className="p-3 bg-gray-50 rounded-lg space-y-2">
                  <div className="flex items-start gap-3">
                    {/* Variant Image */}
                    {variant.image_url && (
                      <div className="flex-shrink-0">
                        <img 
                          src={variant.image_url} 
                          alt={`Variant ${idx + 1}`}
                          className="w-20 h-20 rounded-md object-cover border border-gray-200"
                        />
                      </div>
                    )}
                    
                    {/* Variant Details */}
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">Variant {idx + 1}</Badge>
                          {variant.color && (
                            <Badge className="bg-blue-100 text-blue-800">{variant.color}</Badge>
                          )}
                          {variant.size && (
                            <Badge className="bg-green-100 text-green-800">{variant.size}</Badge>
                          )}
                        </div>
                        {variant.price && (
                          <span className="font-semibold text-blue-600">
                            {product.currency || 'INR'} {variant.price}
                          </span>
                        )}
                      </div>
                      
                      {variant.description && (
                        <p className="text-sm text-gray-600">{variant.description}</p>
                      )}
                      
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        {variant.stock !== undefined && (
                          <span>Stock: {variant.stock}</span>
                        )}
                        {variant.video_url && (
                          <span className="flex items-center gap-1">
                            <Video className="h-3 w-3" />
                            Has video
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {/* Variant Video */}
                  {variant.video_url && (
                    <div className="relative aspect-video bg-gray-900 rounded overflow-hidden">
                      <video src={variant.video_url} controls className="w-full h-full">
                        Your browser does not support video playback.
                      </video>
                    </div>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Videos */}
        {product.video_urls && product.video_urls.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Video className="h-5 w-5" />
                Product Videos ({product.video_urls.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {product.video_urls.map((url, idx) => (
                <div key={idx} className="relative aspect-video bg-gray-900 rounded overflow-hidden">
                  <video src={url} controls className="w-full h-full">
                    Your browser does not support video playback.
                  </video>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Product Info Footer */}
        <Card>
          <CardContent className="pt-6 text-sm text-gray-500 space-y-1">
            <div className="flex justify-between">
              <span>Product ID:</span>
              <span className="font-mono">{product.id}</span>
            </div>
            {product.created_at && (
              <div className="flex justify-between">
                <span>Created:</span>
                <span>{new Date(product.created_at).toLocaleDateString()}</span>
              </div>
            )}
            {product.updated_at && (
              <div className="flex justify-between">
                <span>Updated:</span>
                <span>{new Date(product.updated_at).toLocaleDateString()}</span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Edit Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-md max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Product</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="edit-name">Product Name *</Label>
              <Input
                id="edit-name"
                value={editForm.name}
                onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                placeholder="Enter product name"
              />
            </div>
            <div>
              <Label htmlFor="edit-description">Description</Label>
              <Textarea
                id="edit-description"
                value={editForm.description}
                onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                placeholder="Enter product description"
                rows={4}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="edit-price">Price</Label>
                <Input
                  id="edit-price"
                  type="number"
                  value={editForm.price}
                  onChange={(e) => setEditForm({ ...editForm, price: parseFloat(e.target.value) || 0 })}
                  placeholder="0.00"
                />
              </div>
              <div>
                <Label htmlFor="edit-stock">Stock</Label>
                <Input
                  id="edit-stock"
                  type="number"
                  value={editForm.stock}
                  onChange={(e) => setEditForm({ ...editForm, stock: parseInt(e.target.value) || 0 })}
                  placeholder="0"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="edit-currency">Currency</Label>
              <Input
                id="edit-currency"
                value={editForm.currency}
                onChange={(e) => setEditForm({ ...editForm, currency: e.target.value })}
                placeholder="INR"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={handleSaveEdit} className="flex-1">Save Changes</Button>
            <Button onClick={() => setShowEditDialog(false)} variant="outline">Cancel</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Share Dialog */}
      <Dialog open={showShareDialog} onOpenChange={setShowShareDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Share Product</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-3 py-4">
            <Button
              onClick={() => handleShare('whatsapp')}
              variant="outline"
              className="h-auto py-6 flex-col gap-2 hover:bg-green-50"
            >
              <div className="w-12 h-12 rounded-full bg-green-500 flex items-center justify-center">
                <Share2 className="h-6 w-6 text-white" />
              </div>
              <span>WhatsApp</span>
            </Button>
            <Button
              onClick={() => handleShare('instagram')}
              variant="outline"
              className="h-auto py-6 flex-col gap-2 hover:bg-pink-50"
            >
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                <Share2 className="h-6 w-6 text-white" />
              </div>
              <span>Instagram</span>
            </Button>
            <Button
              onClick={() => handleShare('twitter')}
              variant="outline"
              className="h-auto py-6 flex-col gap-2 hover:bg-blue-50"
            >
              <div className="w-12 h-12 rounded-full bg-blue-500 flex items-center justify-center">
                <Share2 className="h-6 w-6 text-white" />
              </div>
              <span>Twitter</span>
            </Button>
            <Button
              onClick={() => handleShare('facebook')}
              variant="outline"
              className="h-auto py-6 flex-col gap-2 hover:bg-blue-50"
            >
              <div className="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center">
                <Share2 className="h-6 w-6 text-white" />
              </div>
              <span>Facebook</span>
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* List on Marketplace Dialog */}
      <Dialog open={showListDialog} onOpenChange={setShowListDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>List on Marketplace</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 py-4">
            <Button
              onClick={() => handleListOnMarketplace('Amazon')}
              variant="outline"
              className="w-full h-auto py-4 justify-start gap-3 hover:bg-orange-50"
            >
              <div className="w-10 h-10 rounded bg-orange-500 flex items-center justify-center">
                <ShoppingBag className="h-5 w-5 text-white" />
              </div>
              <div className="flex-1 text-left">
                <div className="font-semibold">Amazon</div>
                <div className="text-xs text-gray-500">List on Amazon.in</div>
              </div>
              <ExternalLink className="h-4 w-4 text-gray-400" />
            </Button>
            <Button
              onClick={() => handleListOnMarketplace('Flipkart')}
              variant="outline"
              className="w-full h-auto py-4 justify-start gap-3 hover:bg-blue-50"
            >
              <div className="w-10 h-10 rounded bg-blue-600 flex items-center justify-center">
                <ShoppingBag className="h-5 w-5 text-white" />
              </div>
              <div className="flex-1 text-left">
                <div className="font-semibold">Flipkart</div>
                <div className="text-xs text-gray-500">List on Flipkart.com</div>
              </div>
              <ExternalLink className="h-4 w-4 text-gray-400" />
            </Button>
            <Button
              onClick={() => handleListOnMarketplace('Myntra')}
              variant="outline"
              className="w-full h-auto py-4 justify-start gap-3 hover:bg-pink-50"
            >
              <div className="w-10 h-10 rounded bg-pink-600 flex items-center justify-center">
                <ShoppingBag className="h-5 w-5 text-white" />
              </div>
              <div className="flex-1 text-left">
                <div className="font-semibold">Myntra</div>
                <div className="text-xs text-gray-500">List on Myntra.com</div>
              </div>
              <ExternalLink className="h-4 w-4 text-gray-400" />
            </Button>
          </div>
          <p className="text-xs text-center text-gray-500">
            🚀 Integration coming soon! This will automatically sync your product to these platforms.
          </p>
        </DialogContent>
      </Dialog>
      </div>
    </div>
  );
};

export default ProductDetail;
