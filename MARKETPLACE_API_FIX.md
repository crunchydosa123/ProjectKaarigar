# Marketplace API Fix - 404 Error Resolution

## 🐛 Issue Identified

**Error**: `OPTIONS /api/product/listing/generate HTTP/1.1" 404`

**Root Cause**: Blueprint URL prefix conflict
- `product_bp` was registered with prefix `/api/product`
- `listing_bp` was registered with prefix `/api/product/listing`
- Flask matched `/api/product` first, never reaching `/api/product/listing/*` routes
- CORS preflight (OPTIONS) requests failed with 404

## ✅ Solution Applied

### 1. Backend Changes

#### **File: `backend/app.py`**
Changed blueprint registration:
```python
# BEFORE
app.register_blueprint(listing_bp, url_prefix="/api/product/listing")

# AFTER
app.register_blueprint(listing_bp, url_prefix="/api/marketplace")
```

#### **File: `backend/routes/marketplace_listing.py`**

**Route Changes:**
- `POST /api/product/listing/generate` → `POST /api/marketplace/generate`
- `GET /api/product/marketplace-listings` → `GET /api/marketplace/listings`
- `GET /api/product/listing/<id>/amazon-listing` → `GET /api/marketplace/<id>/amazon-listing`

**Added Extensive Logging:**
- Request details (method, path, headers, body)
- Session data (user_id)
- Firestore operations (query, results)
- Image validation
- File path resolution
- Subprocess execution
- stdout/stderr output

### 2. Frontend Changes

#### **File: `frontend2/src/phone-demo/ProductDetail.tsx`**

**Updated API endpoint:**
```typescript
// BEFORE
const apiUrl = 'http://localhost:5000/api/product/listing/generate';

// AFTER
const apiUrl = 'http://localhost:5000/api/marketplace/generate';
```

**Added comprehensive logging:**
- Request preparation
- API call details
- Response status and data
- Success/error handling
- Complete flow tracking

#### **File: `frontend2/src/phone-demo/MarketplaceListings.tsx`**

**Updated API endpoint:**
```typescript
// BEFORE
const apiUrl = 'http://localhost:5000/api/product/marketplace-listings';

// AFTER
const apiUrl = 'http://localhost:5000/api/marketplace/listings';
```

**Added logging:**
- API call tracking
- Response data
- Listing count

#### **File: `frontend2/src/phone-demo/AmazonListing.tsx`**

**Updated API endpoint:**
```typescript
// BEFORE
const apiUrl = `http://localhost:5000/api/product/${selectedProductId}/amazon-listing`;

// AFTER
const apiUrl = `http://localhost:5000/api/marketplace/${selectedProductId}/amazon-listing`;
```

**Added logging:**
- Product ID tracking
- API call details
- Response data

## 🚀 Next Steps

### Step 1: Restart Backend Server

```powershell
# Stop the current server (Ctrl+C in the terminal)

# Navigate to backend directory
cd D:\Barclays\ProjectKaarigar\backend

# Start the server
python app.py
```

**Verify in logs:**
- ✅ Look for: `"✅ Marketplace listing routes registered"`
- ✅ Verify routes appear: `POST /api/marketplace/generate`, `GET /api/marketplace/listings`

### Step 2: Test End-to-End Flow

1. **Open Product Detail Page**
   - Navigate to any product with images
   - Click "List on Marketplace" button

2. **Select Amazon**
   - Confirm the dialog

3. **Watch Backend Logs**
   Look for:
   ```
   ================================================================================
   📨 MARKETPLACE LISTING GENERATION REQUEST
   ================================================================================
   Request method: POST
   Request path: /api/marketplace/generate
   ```

4. **Watch Frontend Console**
   Open browser DevTools (F12) → Console tab
   Look for:
   ```
   🔵 [Marketplace] Starting listing process...
   🚀 [Marketplace] Calling API...
   📡 [Marketplace] Response received
   ✅ [Marketplace] Listing created successfully!
   ```

5. **Verify in Firestore**
   - Open Firebase Console
   - Navigate to Firestore Database
   - Check `marketplace_listings` collection
   - Verify new document was created

6. **View in Marketplace Listings**
   - Click "View Marketplace Listings" button
   - Verify listing appears
   - Click listing to see Amazon view

### Step 3: Debug if Issues Persist

**If 404 still occurs:**
1. Verify backend server restarted properly
2. Check that blueprint registration shows `/api/marketplace` in logs
3. Look for CORS errors in browser console

**If listing generation fails:**
1. Check backend logs for subprocess output
2. Verify `Model/3_listing_model.py` exists
3. Check `Model/listing_output.json` is created
4. Verify image URLs are accessible

**If Firestore operations fail:**
1. Check authentication (user logged in)
2. Verify Firestore credentials
3. Check `marketplace_listings` collection exists

## 📊 New API Endpoints

All marketplace endpoints are now under `/api/marketplace`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/marketplace/generate` | Generate marketplace listing using AI |
| GET | `/api/marketplace/listings` | Get all user's marketplace listings |
| GET | `/api/marketplace/<product_id>/amazon-listing` | Get Amazon-formatted listing |

## 🔍 Logging Format

### Backend Logs
```
================================================================================
📨 MARKETPLACE LISTING GENERATION REQUEST
================================================================================
Request method: POST
Request path: /api/marketplace/generate
Session data: {'user_id': 'abc123', ...}
Request body: {"product_id": "xyz", "marketplace": "amazon"}

🔍 Fetching product from Firestore...
✅ Product found: "Product Name" ($99.99)
📝 Found 3 images
🚀 Starting listing generation subprocess...
✅ Subprocess completed!
💾 Saved to Firestore: marketplace_listings/doc_id
✅ Listing generated successfully!
```

### Frontend Logs
```
🔵 [Marketplace] Starting listing process...
   Product ID: abc123
   Marketplace: Amazon
✅ [Marketplace] Validation passed
   Product name: Product Name
   Images: 3
🚀 [Marketplace] Calling API...
   URL: http://localhost:5000/api/marketplace/generate
   Method: POST
📡 [Marketplace] Response received
   Status: 200
   OK: true
✅ [Marketplace] Listing created successfully!
🏁 [Marketplace] Process completed
```

## 📝 Files Modified

### Backend
1. `backend/app.py` - Blueprint registration
2. `backend/routes/marketplace_listing.py` - Routes and logging

### Frontend
1. `frontend2/src/phone-demo/ProductDetail.tsx` - API endpoint and logging
2. `frontend2/src/phone-demo/MarketplaceListings.tsx` - API endpoint and logging
3. `frontend2/src/phone-demo/AmazonListing.tsx` - API endpoint and logging

## ⚠️ Important Notes

1. **All changes must be applied** - Both backend and frontend need the new endpoints
2. **Server restart required** - Flask doesn't hot-reload blueprint changes
3. **Clear browser cache** - May need to hard refresh (Ctrl+Shift+R)
4. **Check console logs** - Extensive logging added for debugging

## 🎯 Success Criteria

✅ No 404 errors on `/api/marketplace/generate`  
✅ Backend logs show complete request flow  
✅ Frontend logs show API calls and responses  
✅ Listing saved to Firestore  
✅ listing_output.json generated  
✅ Marketplace Listings page shows new listing  
✅ Amazon Listing page displays correctly  

---

**Created**: 2024
**Issue**: Blueprint URL prefix conflict causing 404
**Resolution**: Changed `/api/product/listing` → `/api/marketplace`
