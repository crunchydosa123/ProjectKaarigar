# Amazon Marketplace Integration

## 🎯 Overview
This feature allows users to list their products on Amazon (and other marketplaces) directly from the Kaarigar app, with AI-generated optimized listings.

## 📋 Features

### 1. **Product Detail Page → List on Marketplace**
- Click "List on Marketplace" button
- Choose platform (Amazon/Flipkart/Myntra)
- AI generates optimized listing using `listing_model`
- Saves to Firestore `marketplace_listings` collection

### 2. **Marketplace Listings Page**
- View all products listed on marketplaces
- Filter by platform
- See listing status (active/pending/draft)
- View statistics (views, etc.)
- Click to view on respective platform

### 3. **Amazon-like Product View**
- Pixel-perfect Amazon mobile UI replica
- Product images carousel
- Ratings & reviews display
- Price with discounts
- Bullet points
- Product description
- Technical specifications
- Add to Cart / Buy Now buttons

## 🔄 Complete Flow

```
User Flow:
1. User creates product → Add Product page
2. Product has images → Required for listing
3. User opens Product Detail page
4. Clicks "List on Marketplace" button
5. Selects "Amazon" from dialog
6. Backend calls listing_model.py with:
   - Product images URLs
   - Product name
   - Product price
   - Product description
7. listing_model generates optimized listing:
   - SEO-optimized title
   - Compelling bullet points
   - Detailed description
   - Technical specifications
   - Price recommendations
8. Listing saved to Firestore
9. User redirected to Marketplace Listings page
10. User clicks on Amazon listing
11. Opens Amazon-like product view
```

## 🛠️ Technical Implementation

### Backend (`routes/marketplace_listing.py`)

**Endpoints:**
```
POST   /api/product/listing/generate
GET    /api/product/marketplace-listings
GET    /api/product/listing/<product_id>/amazon-listing
```

**Key Functions:**
- `generate_listing()` - Calls `3_listing_model.py` subprocess
- Reads product data from Firestore
- Passes image URLs and product info to listing model
- Stores generated listing in `marketplace_listings` collection

### Frontend Components

**1. MarketplaceListings.tsx**
- Lists all marketplace listings
- Shows platform logos
- Status badges
- View statistics

**2. AmazonListing.tsx**
- Amazon UI replica
- Product images carousel
- Pricing display
- Bullet points
- Specifications
- Add to Cart/Buy Now

**3. ProductDetail.tsx**
- Updated `handleListOnMarketplace()` function
- Calls backend API
- Shows loading state
- Redirects to listings page

### Integration with listing_model

**Input to listing_model:**
```python
input_text = f"{','.join(image_urls)}\n\n{product_name}\n{marketplace}\n{price}\n\n\n"
```

**Output from listing_model:**
```json
{
  "listing": {
    "title": "SEO optimized title",
    "bullets": ["bullet 1", "bullet 2", ...],
    "description": "detailed description",
    "specifications": {"key": "value"},
    "seo_tags": ["tag1", "tag2"],
    "pricing": {
      "ai_price": 999,
      "recommended_range": [899, 1099]
    }
  }
}
```

## 📁 File Structure

```
backend/
├── routes/
│   └── marketplace_listing.py       # New marketplace routes
└── app.py                           # Register listing_bp

frontend2/src/phone-demo/
├── AmazonListing.tsx                # Amazon UI replica
├── MarketplaceListings.tsx          # Listings overview
├── ProductDetail.tsx                # Updated with list function
├── ListProducts.tsx                 # Added marketplace listings button
└── index.tsx                        # Added routes

Model/
└── 3_listing_model.py               # Updated to accept URLs
```

## 🎨 UI Components

### Amazon Listing Page Features:
✅ Amazon-style header with logo
✅ Search bar (disabled/placeholder)
✅ Product image carousel
✅ Star ratings display
✅ Price with discount calculation
✅ Stock availability
✅ Delivery date
✅ Bullet points (About this item)
✅ Product description
✅ Technical specifications
✅ Seller information
✅ Add to Cart / Buy Now buttons
✅ Wishlist & Share options

### Marketplace Listings Page Features:
✅ Product cards with images
✅ Platform logos (Amazon/Flipkart)
✅ Status badges (active/pending/draft)
✅ View count
✅ Listed date
✅ Quick view button

## 🔥 Key Features

### 1. **AI-Powered Listing Generation**
- Uses Gemini AI through listing_model
- Analyzes product images
- Generates SEO-optimized content
- Platform-specific optimization

### 2. **Firestore Schema**

**Collection: `marketplace_listings`**
```javascript
{
  product_id: string,
  user_id: string,
  marketplace: 'amazon' | 'flipkart',
  status: 'active' | 'pending' | 'draft',
  listing_data: {
    title: string,
    bullets: string[],
    description: string,
    specifications: object,
    ...
  },
  product_name: string,
  price: number,
  image_url: string,
  listed_at: timestamp,
  views: number
}
```

### 3. **Real Amazon UI Clone**
- Matches Amazon's mobile interface
- Orange/black color scheme
- Proper spacing and typography
- Carousel navigation
- Responsive images

## 🚀 Usage

### List Product on Amazon:
```typescript
1. Open product detail page
2. Click "List on Marketplace"
3. Select "Amazon"
4. Wait for AI generation (30-60s)
5. View success message
6. Check Marketplace Listings page
```

### View Amazon Listing:
```typescript
1. Open Marketplace Listings page
2. Find your Amazon listing
3. Click "View on Amazon"
4. See full Amazon-like product page
```

## 🔄 API Calls Flow

```
Frontend → Backend → listing_model → Backend → Firestore → Frontend

1. POST /api/product/listing/generate
   ↓
2. Get product from Firestore
   ↓
3. Run subprocess: python 3_listing_model.py
   ↓
4. Parse listing_output.json
   ↓
5. Save to marketplace_listings collection
   ↓
6. Return success + listing_id
   ↓
7. Frontend redirects to marketplace listings
```

## 📊 Data Flow

```
Product (Firestore)
  → image_urls, name, price, description
    → listing_model (AI Generation)
      → listing_output.json
        → marketplace_listings (Firestore)
          → AmazonListing component
```

## 🎯 Future Enhancements

- [ ] Add Flipkart UI replica
- [ ] Add Myntra UI replica  
- [ ] Real marketplace API integration
- [ ] Order tracking
- [ ] Inventory sync
- [ ] Price optimization suggestions
- [ ] A/B testing for listings
- [ ] Performance analytics
- [ ] Automatic repricing

## 🐛 Troubleshooting

**Issue: Listing generation timeout**
- Check if listing_model.py is accessible
- Verify Python environment
- Check Gemini API key
- Increase timeout in marketplace_listing.py

**Issue: No images in Amazon view**
- Verify product has image_urls
- Check GCS URLs are public
- Verify image URL format

**Issue: Listings not showing**
- Check user_id in session
- Verify Firestore permissions
- Check console for errors

## 📝 Notes

- Listing generation takes 30-60 seconds
- Requires at least 1 product image
- AI content quality depends on image quality
- Currently generates dummy reviews/ratings
- Marketplace integration is simulated (not live)
