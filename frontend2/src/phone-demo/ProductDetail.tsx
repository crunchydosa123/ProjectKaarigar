import React, { useState, useEffect } from 'react';
import { usePage } from '@/contexts/PageContext';
import { ChevronLeft, Edit2, Share2, ShoppingBag, Package, Image as ImageIcon, Video, ExternalLink, Upload, X, Check, Loader2, ImagePlus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { productAPI, mediaAPI } from '@/lib/api';

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
  ai_generated_title?: string;
  ai_generated_description?: string;
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
  const [aiGenerating, setAiGenerating] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  
  // Media picker states
  const [availableImages, setAvailableImages] = useState<{ id: string; title: string; public_url: string }[]>([]);
  const [availableVideos, setAvailableVideos] = useState<{ id: string; title: string; public_url: string }[]>([]);
  const [showMediaChoiceDialog, setShowMediaChoiceDialog] = useState(false);
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [showSelectMediaDialog, setShowSelectMediaDialog] = useState(false);
  const [currentMediaType, setCurrentMediaType] = useState<'image' | 'video'>('image');
  const [currentVariantIndexForMedia, setCurrentVariantIndexForMedia] = useState<number>(-1);
  const [uploadingFiles, setUploadingFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: boolean }>({});
  
  // Edit form state
  const [editForm, setEditForm] = useState({
    name: '',
    description: '',
    price: 0,
    stock: 0,
    currency: 'INR',
    variants: [] as Variant[],
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
              currency: foundProduct.currency || 'INR',
              variants: ((foundProduct as any).variants || []).map((v: Variant) => ({ ...v }))
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
    setValidationErrors([]); // Clear validation errors when opening edit dialog
    setShowEditDialog(true);
  };

  const validateForm = (): boolean => {
    const errors: string[] = [];

    // Validate product name
    if (!editForm.name || editForm.name.trim().length === 0) {
      errors.push('Product name is required');
    }

    // Validate price
    if (editForm.price < 0) {
      errors.push('Price cannot be negative');
    }

    // Validate stock
    if (editForm.stock < 0) {
      errors.push('Stock cannot be negative');
    }

    // Validate variants
    if (editForm.variants && editForm.variants.length > 0) {
      editForm.variants.forEach((variant, idx) => {
        const variantNum = idx + 1;
        
        // Validate variant price
        const variantPrice = typeof variant.price === 'string' ? parseFloat(variant.price) : (variant.price || 0);
        if (variantPrice < 0) {
          errors.push(`Variant ${variantNum}: Price cannot be negative`);
        }

        // Validate variant stock
        const variantStock = typeof variant.stock === 'string' ? parseInt(variant.stock) : (variant.stock || 0);
        if (variantStock < 0) {
          errors.push(`Variant ${variantNum}: Stock cannot be negative`);
        }

        // Validate image URL if provided
        if (variant.image_url && variant.image_url.trim().length > 0) {
          try {
            new URL(variant.image_url);
          } catch {
            errors.push(`Variant ${variantNum}: Invalid image URL format`);
          }
        }

        // Validate video URL if provided
        if (variant.video_url && variant.video_url.trim().length > 0) {
          try {
            new URL(variant.video_url);
          } catch {
            errors.push(`Variant ${variantNum}: Invalid video URL format`);
          }
        }
      });
    }

    setValidationErrors(errors);
    return errors.length === 0;
  };

  const handleSaveEdit = async () => {
    // Validate form before submitting
    if (!validateForm()) {
      return; // Validation errors will be shown in UI
    }

    try {
      setLoading(true);
      setValidationErrors([]); // Clear any previous errors
      
      // Call backend update route
      if (!productId) throw new Error('Missing product id');
      const payload = {
        name: editForm.name,
        description: editForm.description,
        price: editForm.price,
        stock: editForm.stock,
        currency: editForm.currency,
        variants: editForm.variants || []
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

  // Variant helpers for edit dialog
  const handleAddVariant = () => {
    setEditForm({
      ...editForm,
      variants: [
        ...(editForm.variants || []),
        { description: '', color: '', size: '', price: 0, stock: 0, image_url: '', video_url: '' }
      ]
    });
  };

  const handleRemoveVariant = (index: number) => {
    const v = [...(editForm.variants || [])];
    v.splice(index, 1);
    setEditForm({ ...editForm, variants: v });
  };

  const handleVariantChange = (index: number, key: keyof Variant, value: any) => {
    const v = [...(editForm.variants || [])];
    v[index] = { ...v[index], [key]: value };
    setEditForm({ ...editForm, variants: v });
  };

  // Media selection helpers
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

  const handleChooseMedia = (variantIndex: number, mediaType: 'image' | 'video') => {
    setCurrentVariantIndexForMedia(variantIndex);
    setCurrentMediaType(mediaType);
    setShowMediaChoiceDialog(true);
    loadMediaChoices();
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

      // Add uploaded media to variant
      if (currentVariantIndexForMedia >= 0 && uploadedUrls.length > 0) {
        const updated = [...(editForm.variants || [])];
        if (currentMediaType === 'image') {
          updated[currentVariantIndexForMedia].image_url = uploadedUrls[0];
        } else {
          updated[currentVariantIndexForMedia].video_url = uploadedUrls[0];
        }
        setEditForm({ ...editForm, variants: updated });
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

  const handleSelectExistingMedia = (mediaUrl: string) => {
    if (currentVariantIndexForMedia >= 0) {
      const updated = [...(editForm.variants || [])];
      if (currentMediaType === 'image') {
        updated[currentVariantIndexForMedia].image_url = mediaUrl;
      } else {
        updated[currentVariantIndexForMedia].video_url = mediaUrl;
      }
      setEditForm({ ...editForm, variants: updated });
    }
    setShowSelectMediaDialog(false);
    setShowMediaChoiceDialog(false);
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

  const handleListOnMarketplace = async (marketplace: string) => {
    console.log('🔵 [Marketplace] Starting listing process...');
    console.log('   Product ID:', productId);
    console.log('   Marketplace:', marketplace);
    console.log('   Product object:', product);
    console.log('   Product exists:', !!product);
    console.log('   ProductId exists:', !!productId);
    
    if (!product || !productId) {
      console.error('❌ [Marketplace] Product not found');
      console.error('   Product:', product);
      console.error('   ProductId:', productId);
      alert('Product not found');
      return;
    }

    if (!product.image_urls || product.image_urls.length === 0) {
      console.error('❌ [Marketplace] No images found');
      alert('Product must have at least one image to list on marketplace');
      return;
    }

    console.log('✅ [Marketplace] Validation passed');
    console.log('   Product name:', product.name);
    console.log('   Images:', product.image_urls.length);

    const confirmed = confirm(`List "${product.name}" on ${marketplace}?\n\nThis will generate an optimized listing using AI.`);
    if (!confirmed) {
      console.log('⚠️ [Marketplace] User cancelled');
      return;
    }

    try {
      setLoading(true);
      const apiUrl = 'https://backend-557742533869.asia-south1.run.app/api/marketplace/generate';
      //const apiUrl = '/api/marketplace/generate';
      const requestBody = {
        product_id: productId,
        marketplace: marketplace.toLowerCase()
      };

      console.log('🚀 [Marketplace] Calling API...');
      console.log('   URL:', apiUrl);
      console.log('   Method: POST');
      console.log('   Body:', JSON.stringify(requestBody, null, 2));

      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(requestBody)
      });

      console.log('📡 [Marketplace] Response received');
      console.log('   Status:', response.status);
      console.log('   Status Text:', response.statusText);
      console.log('   OK:', response.ok);

      const data = await response.json();
      console.log('📄 [Marketplace] Response data:', JSON.stringify(data, null, 2));

      if (data.success) {
        console.log('✅ [Marketplace] Listing created successfully!');
        alert(`✅ Successfully listed on ${marketplace}!\n\nYou can now view it in Marketplace Listings.`);
        setShowListDialog(false);
        // Optionally redirect to marketplace listings
        setCurrentPage('marketplace-listings');
      } else {
        console.error('❌ [Marketplace] API returned failure:', data);
        throw new Error(data.error || 'Failed to list product');
      }
    } catch (err: any) {
      console.error('❌ [Marketplace] Error occurred:');
      console.error('   Message:', err.message);
      console.error('   Full error:', err);
      alert('Failed to list product: ' + (err.message || err));
    } finally {
      setLoading(false);
      console.log('🏁 [Marketplace] Process completed');
    }
  };

  const handleGenerateAI = async () => {
    if (!product || !productId) {
      alert('Product not found');
      return;
    }

    if (!product.image_urls || product.image_urls.length === 0) {
      alert('Product must have at least one image for AI generation');
      return;
    }

    try {
      setAiGenerating(true);
      const response = await productAPI.generateAI(productId);
      
      if (response && response.success) {
        // Update local product state with AI-generated content
        setProduct({
          ...product,
          ai_generated_title: response.ai_generated_title,
          ai_generated_description: response.ai_generated_description,
        } as any);
        
        alert('AI content generated successfully!');
      } else {
        throw new Error((response as any)?.error || 'AI generation failed');
      }
    } catch (err: any) {
      console.error('AI generation failed:', err);
      alert('AI generation failed: ' + (err.message || err));
    } finally {
      setAiGenerating(false);
    }
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

        {/* AI Generation Button */}
        <Button
          onClick={handleGenerateAI}
          className="w-full h-auto py-4 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
          disabled={aiGenerating || !product.image_urls || product.image_urls.length === 0}
        >
          {aiGenerating ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-2"></div>
              Generating AI Content...
            </>
          ) : (
            <>
              <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Generate AI Title & Description
            </>
          )}
        </Button>

        {/* AI Generated Content Display */}
        {((product as any).ai_generated_title || (product as any).ai_generated_description) && (
          <Card className="border-purple-200 bg-purple-50">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <svg className="h-5 w-5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                AI-Generated Content
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {(product as any).ai_generated_title && (
                <div>
                  <h4 className="font-semibold text-sm text-purple-700 mb-1">AI Title</h4>
                  <p className="text-gray-800">{(product as any).ai_generated_title}</p>
                </div>
              )}
              {(product as any).ai_generated_description && (
                <div>
                  <h4 className="font-semibold text-sm text-purple-700 mb-1">AI Description</h4>
                  <p className="text-gray-700 whitespace-pre-wrap">{(product as any).ai_generated_description}</p>
                </div>
              )}
            </CardContent>
          </Card>
        )}

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

          {/* Validation Errors */}
          {validationErrors.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 space-y-1">
              <p className="font-semibold text-red-800 text-sm">Please fix the following errors:</p>
              <ul className="list-disc list-inside text-red-700 text-sm space-y-1">
                {validationErrors.map((error, idx) => (
                  <li key={idx}>{error}</li>
                ))}
              </ul>
            </div>
          )}

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
            {/* Variants editor */}
            <div>
              <div className="flex items-center justify-between">
                <h4 className="font-semibold">Variants</h4>
                <Button variant="ghost" size="sm" onClick={handleAddVariant}>Add Variant</Button>
              </div>
              <div className="space-y-3 mt-3">
                {editForm.variants && editForm.variants.length > 0 ? (
                  editForm.variants.map((variant, idx) => (
                    <div key={idx} className="p-3 bg-gray-50 rounded-lg">
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <Label>Color</Label>
                          <Input value={variant.color || ''} onChange={(e) => handleVariantChange(idx, 'color', e.target.value)} />
                        </div>
                        <div>
                          <Label>Size</Label>
                          <Input value={variant.size || ''} onChange={(e) => handleVariantChange(idx, 'size', e.target.value)} />
                        </div>
                        <div>
                          <Label>Price</Label>
                          <Input type="number" value={variant.price as any || 0} onChange={(e) => handleVariantChange(idx, 'price', parseFloat(e.target.value) || 0)} />
                        </div>
                        <div>
                          <Label>Stock</Label>
                          <Input type="number" value={variant.stock as any || 0} onChange={(e) => handleVariantChange(idx, 'stock', parseInt(e.target.value) || 0)} />
                        </div>
                        <div className="col-span-2">
                          <Label>Description</Label>
                          <Input value={variant.description || ''} onChange={(e) => handleVariantChange(idx, 'description', e.target.value)} />
                        </div>
                        <div className="col-span-2">
                          <Label>Variant Image</Label>
                          <Button
                            variant="outline"
                            size="sm"
                            type="button"
                            onClick={() => handleChooseMedia(idx, 'image')}
                            className="w-full flex gap-2"
                          >
                            <ImagePlus className="w-4 h-4" />
                            Choose Image
                          </Button>
                          {variant.image_url && (
                            <div className="relative mt-2 w-24">
                              <img
                                src={variant.image_url}
                                alt="variant preview"
                                className="w-24 h-24 object-cover rounded-md border"
                              />
                              <Button
                                variant="destructive"
                                size="icon"
                                type="button"
                                className="absolute -top-2 -right-2 h-6 w-6 rounded-full"
                                onClick={() => handleVariantChange(idx, 'image_url', '')}
                              >
                                <X className="w-3 h-3" />
                              </Button>
                            </div>
                          )}
                        </div>
                        <div className="col-span-2">
                          <Label>Variant Video</Label>
                          <Button
                            variant="outline"
                            size="sm"
                            type="button"
                            onClick={() => handleChooseMedia(idx, 'video')}
                            className="w-full flex gap-2"
                          >
                            <ImagePlus className="w-4 h-4" />
                            Choose Video
                          </Button>
                          {variant.video_url && (
                            <div className="relative mt-2 w-32">
                              <video
                                src={variant.video_url}
                                className="w-32 h-20 object-cover rounded-md border"
                                controls
                              />
                              <Button
                                variant="destructive"
                                size="icon"
                                type="button"
                                className="absolute -top-2 -right-2 h-6 w-6 rounded-full"
                                onClick={() => handleVariantChange(idx, 'video_url', '')}
                              >
                                <X className="w-3 h-3" />
                              </Button>
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="flex justify-end mt-2">
                        <Button variant="destructive" size="sm" onClick={() => handleRemoveVariant(idx)}>Remove</Button>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-gray-500">No variants added.</p>
                )}
              </div>
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

      {/* Media Choice Dialog - Shows "Upload" or "Select Existing" options */}
      <Dialog open={showMediaChoiceDialog} onOpenChange={setShowMediaChoiceDialog}>
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
                setShowMediaChoiceDialog(false);
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
                setShowMediaChoiceDialog(false);
                setShowSelectMediaDialog(true);
              }}
            >
              <ImagePlus className="w-5 h-5" />
              Select from Existing {currentMediaType === 'image' ? 'Images' : 'Videos'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Select Existing Media Dialog */}
      <Dialog open={showSelectMediaDialog} onOpenChange={setShowSelectMediaDialog}>
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
                    onClick={() => handleSelectExistingMedia(img.public_url)}
                    className="border-2 border-gray-200 rounded-lg p-1 hover:border-blue-500 transition"
                  >
                    <img src={img.public_url} alt={img.title} className="w-full h-24 object-cover rounded" />
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
                    onClick={() => handleSelectExistingMedia(vid.public_url)}
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
    </div>
  );
};

export default ProductDetail;
