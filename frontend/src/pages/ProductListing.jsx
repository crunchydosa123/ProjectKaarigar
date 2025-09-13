import React, { useState, useRef, useEffect } from "react";
import { Search, Upload, Plus, X, ArrowLeft } from "lucide-react";
import MenuDrawer from "../components/MenuDrawer";

const API_BASE = "http://localhost:5000/api"; // adjust if your backend is hosted elsewhere

export default function MobileProductListings() {
  const [products, setProducts] = useState([]);
  const [query, setQuery] = useState("");
  const [detail, setDetail] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);

  // Add-product form state
  const [pName, setPName] = useState("");
  const [pPrice, setPPrice] = useState("");
  const [pShort, setPShort] = useState("");
  const [pImages, setPImages] = useState([]); // { file, url }
  const [pVideo, setPVideo] = useState(null);
  const [addSheetOpen, setAddSheetOpen] = useState(false);

  const [optimizing, setOptimizing] = useState(false);
  const [optError, setOptError] = useState(null);

  const imageInputRef = useRef(null);
  const videoInputRef = useRef(null);

  // Handle multiple image uploads
  const handleImagesChange = (e) => {
    const files = e.target.files;
    if (!files) return;

    const newPreviews = Array.from(files).map((file) => ({
      file,
      url: URL.createObjectURL(file),
    }));

    setPImages((prev) => [...prev, ...newPreviews]);
  };

  // Handle video upload
  const handleVideoChange = (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    setPVideo({
      file,
      url: URL.createObjectURL(file),
    });
  };

  // Add product submit — now uploads to backend for optimization
  const handleAddProductSubmit = async (e) => {
    e.preventDefault();
    setOptError(null);

    if (!pName.trim() || !pPrice || !pShort.trim()) {
      alert("Please enter name, price and description.");
      return;
    }

    try {
      setOptimizing(true);

      // Build FormData
      const fd = new FormData();
      fd.append("description", pShort.trim());
      fd.append("price", pPrice);
      fd.append("currency", "INR"); // change if needed
      // include original name as optional hint
      fd.append("original_name", pName.trim());

      // Append files
      pImages.forEach((p) => {
        if (p && p.file) {
          fd.append("images", p.file);
        }
      });

      // If you want to include video, backend must support it — currently product optimize route expects images only
      // if (pVideo && pVideo.file) fd.append("video", pVideo.file);

      const res = await fetch(`${API_BASE}/product/optimize`, {
        method: "POST",
        body: fd,
      });

      if (!res.ok) {
        const text = await res.text().catch(() => null);
        throw new Error(`Server error ${res.status}: ${text || res.statusText}`);
      }

      const data = await res.json();

      // Build new product entry from returned optimization (fallback to local data)
      const prodId = data.product_id || Date.now();
      const suggestedName = data.suggested_name || pName.trim();
      const suggestedDescription = data.suggested_description || pShort.trim();
      const suggestedPrice = (data.suggested_price !== undefined && data.suggested_price !== null)
        ? data.suggested_price
        : Number(pPrice);

      // prefer server-hosted image URLs if available, otherwise use local preview urls
      const imagesFromServer = data.image_urls && data.image_urls.length > 0 ? data.image_urls : pImages.map(i => i.url);

      const newProd = {
        id: prodId,
        name: suggestedName,
        price: suggestedPrice,
        short: suggestedDescription,
        images: imagesFromServer,
        video: pVideo ? pVideo.url : null,
        meta: {
          original_name: pName,
          original_price: Number(pPrice),
        },
        optimized: {
          product_json_url: data.product_json_url || null,
          seo_tags: data.seo_tags || [],
          price_reasoning: data.price_reasoning || "",
        },
      };

      setProducts((prev) => [newProd, ...prev]);

      // reset form — revoke local preview URLs
      pImages.forEach((img) => {
        try {
          URL.revokeObjectURL(img.url);
        } catch { }
      });
      if (pVideo) {
        try { URL.revokeObjectURL(pVideo.url); } catch { }
      }

      setPName("");
      setPPrice("");
      setPShort("");
      setPImages([]);
      setPVideo(null);
      setAddSheetOpen(false);
    } catch (err) {
      console.error("Optimization error:", err);
      setOptError(err.message || "Failed to optimize product");
      alert(`Optimize failed: ${err.message || err}`);
    } finally {
      setOptimizing(false);
    }
  };

  // Cleanup all blob URLs only on component unmount
  useEffect(() => {
    return () => {
      // Revoke URLs from all products (they may be server URLs or local previews)
      products.forEach((product) => {
        (product.images || []).forEach((url) => {
          // only revoke if it looks like an object URL
          if (url && url.startsWith("blob:")) {
            try { URL.revokeObjectURL(url); } catch { }
          }
        });
        if (product.video && product.video.startsWith("blob:")) {
          try { URL.revokeObjectURL(product.video); } catch { }
        }
      });
      // Revoke any remaining form previews
      pImages.forEach((img) => {
        if (img && img.url && img.url.startsWith("blob:")) {
          try { URL.revokeObjectURL(img.url); } catch { }
        }
      });
      if (pVideo && pVideo.url && pVideo.url.startsWith("blob:")) {
        try { URL.revokeObjectURL(pVideo.url); } catch { }
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filtered = products.filter(
    (p) =>
      p.name.toLowerCase().includes(query.toLowerCase()) ||
      p.short.toLowerCase().includes(query.toLowerCase())
  );

  if (detail) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-100 via-blue-50 to-pink-100 overflow-hidden relative p-4">
        {/* Floating background blobs */}
        <div className="absolute top-10 left-10 transform -translate-x-1/2 w-72 h-72 bg-gradient-to-br from-purple-300 to-pink-300 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse md:transform-none" />
        <div className="absolute top-20 right-10 w-64 h-64 bg-gradient-to-br from-blue-300 to-purple-300 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse delay-1000 hidden md:block" />
        <div className="absolute bottom-10 left-1/2 w-80 h-80 bg-gradient-to-br from-pink-300 to-blue-300 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse delay-2000" />

        {/* Details Header */}
        <div className="flex items-center gap-3 mb-6 relative z-10">
          <button
            className="p-2 rounded-lg bg-white shadow-md"
            onClick={() => setDetail(null)}
          >
            <ArrowLeft className="w-5 h-5 text-gray-700" />
          </button>
          <h2 className="text-lg font-semibold flex-1 text-center">Product Details</h2>
        </div>

        {/* Product Details Content */}
        <div className="bg-white rounded-2xl shadow-sm p-4 relative z-10">
          <div className="mb-3">
            <h2 className="text-lg font-semibold">{detail.name}</h2>
            <div className="text-sm text-gray-500">₹{detail.price}</div>
          </div>

          <div className="w-full h-56 bg-gray-100 mb-3 overflow-hidden rounded-xl flex gap-2">
            {detail.images?.map((url, idx) => (
              <img key={idx} src={url} alt={`product-${idx}`} className="w-1/2 h-full object-cover rounded" />
            ))}
          </div>

          {detail.video && (
            <div className="w-full mb-3">
              <video src={detail.video} className="w-full rounded-lg" controls />
            </div>
          )}

          <p className="text-sm text-gray-700 mb-3">{detail.short}</p>

          {detail.optimized?.product_json_url && (
            <div className="mt-4">
              <a
                href={detail.optimized.product_json_url}
                target="_blank"
                rel="noreferrer"
                className="inline-block bg-gradient-to-br from-blue-500 to-purple-500 text-white px-4 py-2 rounded-2xl shadow hover:shadow-lg"
              >
                View Optimized JSON
              </a>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-100 via-blue-50 to-pink-100 overflow-hidden relative p-4">
      {/* Floating background blobs (adapted from Conversational AI page) */}
      <div className="absolute top-10 left-10 transform -translate-x-1/2 w-72 h-72 bg-gradient-to-br from-purple-300 to-pink-300 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse md:transform-none" />
      <div className="absolute top-20 right-10 w-64 h-64 bg-gradient-to-br from-blue-300 to-purple-300 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse delay-1000 hidden md:block" />
      <div className="absolute bottom-10 left-1/2 w-80 h-80 bg-gradient-to-br from-pink-300 to-blue-300 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse delay-2000" />

      {/* Header */}
      <div className="flex items-center gap-3 mb-6 relative z-10">
        <button
          className="p-2 rounded-lg bg-white shadow-md"
          onClick={() => setMenuOpen(true)}
        >
          <svg
            className="w-5 h-5 text-gray-700"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <div className="flex-1 relative">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search products"
            className="w-full h-12 px-4 rounded-xl border border-gray-200 bg-white shadow-sm focus:outline-none"
          />
          <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        </div>

        <button
          onClick={() => setAddSheetOpen(true)}
          className="ml-2 inline-flex items-center justify-center h-12 w-12 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-md"
          aria-label="Add product"
        >
          <Plus className="w-5 h-5" />
        </button>
      </div>

      {/* Product grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 relative z-10">
        {filtered.length === 0 ? (
          <div className="col-span-full text-center text-gray-500 py-12">
            No products — tap + to add one.
          </div>
        ) : (
          filtered.map((p) => (
            <article key={p.id} className="bg-white rounded-2xl shadow-sm overflow-hidden">
              <button className="w-full block text-left" onClick={() => setDetail(p)}>
                <div className="w-full h-44 bg-gray-100 overflow-hidden">
                  {p.images?.length > 0 ? (
                    <img src={p.images[0]} alt={p.name} className="w-full h-full object-cover" />
                  ) : (
                    <div className="flex items-center justify-center w-full h-full text-gray-400">
                      No image
                    </div>
                  )}
                </div>
                <div className="p-3">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="text-sm font-semibold text-gray-800">{p.name}</h3>
                    <div className="text-sm font-semibold">₹{p.price}</div>
                  </div>
                  <p className="text-xs text-gray-500 mb-2 truncate">{p.short}</p>
                  {p.optimized?.seo_tags?.length > 0 && (
                    <div className="flex gap-2 flex-wrap">
                      {p.optimized.seo_tags.slice(0, 3).map((t, i) => (
                        <span key={i} className="text-xs bg-gray-100 px-2 py-1 rounded-md text-gray-600">{t}</span>
                      ))}
                    </div>
                  )}
                </div>
              </button>
            </article>
          ))
        )}
      </div>

      {/* Add Product sheet */}
      <div
        className={`fixed left-0 right-0 bottom-0 z-60 transition-transform duration-300 ${addSheetOpen ? "translate-y-0" : "translate-y-full"}`}
        aria-hidden={!addSheetOpen}
      >
        <div className="max-w-xl mx-auto bg-white/98 backdrop-blur-xl rounded-t-3xl shadow-2xl p-4 text-black">
          <div className="flex items-center justify-between mb-3">
            <div className="text-lg font-semibold">Add Product</div>
            <button onClick={() => setAddSheetOpen(false)} className="p-2 rounded-lg">
              <X className="w-5 h-5" />
            </button>
          </div>

          <form onSubmit={handleAddProductSubmit} className="space-y-3">
            {/* Images */}
            <div>
              <label className="text-sm font-medium">Photos</label>
              <div className="mt-2 flex gap-3 flex-wrap">
                {pImages.map((img, idx) => (
                  <div key={idx} className="w-20 h-20 bg-gray-100 rounded-xl overflow-hidden relative">
                    <img src={img.url} alt={`preview-${idx}`} className="w-full h-full object-cover" />
                    <button
                      type="button"
                      onClick={() => {
                        // revoke and remove preview
                        try { URL.revokeObjectURL(img.url); } catch { }
                        setPImages((prev) => prev.filter((_, i) => i !== idx));
                      }}
                      className="absolute top-1 right-1 bg-white rounded-full p-1 shadow"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
                <label htmlFor="add-photos" className="w-20 h-20 flex items-center justify-center bg-gray-100 rounded-xl cursor-pointer">
                  <Upload className="w-7 h-7 text-gray-400" />
                </label>
                <input ref={imageInputRef} type="file" accept="image/*" multiple onChange={handleImagesChange} className="hidden" id="add-photos" />
              </div>
            </div>

            {/* Video */}
            <div>
              <label className="text-sm font-medium">Video (optional)</label>
              <div className="mt-2">
                {pVideo ? (
                  <div className="relative w-40 h-28 bg-gray-100 rounded-lg overflow-hidden">
                    <video src={pVideo.url} className="w-full h-full object-cover" controls />
                    <button type="button" onClick={() => { try { URL.revokeObjectURL(pVideo.url); } catch { }; setPVideo(null); }} className="absolute top-1 right-1 bg-white rounded-full p-1 shadow">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <>
                    <label htmlFor="add-video" className="px-3 py-2 rounded-lg bg-white border border-gray-200 cursor-pointer inline-block">Choose video</label>
                    <input ref={videoInputRef} type="file" accept="video/*" onChange={handleVideoChange} className="hidden" id="add-video" />
                  </>
                )}
              </div>
            </div>

            {/* Name */}
            <div>
              <label className="text-sm font-medium">Name</label>
              <input value={pName} onChange={(e) => setPName(e.target.value)} className="w-full mt-2 px-3 py-2 rounded-lg border border-gray-200" placeholder="Product name" />
            </div>

            {/* Price */}
            <div>
              <label className="text-sm font-medium">Selling Price (₹)</label>
              <input value={pPrice} onChange={(e) => setPPrice(e.target.value)} type="number" className="w-full mt-2 px-3 py-2 rounded-lg border border-gray-200" placeholder="e.g. 2499" />
            </div>

            {/* Short description */}
            <div>
              <label className="text-sm font-medium">Short description</label>
              <input value={pShort} onChange={(e) => setPShort(e.target.value)} className="w-full mt-2 px-3 py-2 rounded-lg border border-gray-200" placeholder="One-liner for list view" />
            </div>

            {optError && <div className="text-sm text-red-600">{optError}</div>}

            <div className="flex items-center justify-between">
              <button type="button" onClick={() => { setPName(""); setPPrice(""); setPShort(""); pImages.forEach(i => { try { URL.revokeObjectURL(i.url); } catch { } }); setPImages([]); setPVideo(null); setAddSheetOpen(false); }} className="px-4 py-2 rounded-lg bg-gray-100">
                Cancel
              </button>
              <button type="submit" className={`px-4 py-2 rounded-lg ${optimizing ? "bg-gray-400 text-white cursor-wait" : "bg-purple-600 text-white"}`} disabled={optimizing}>
                {optimizing ? "Optimizing..." : "Add product"}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Menu drawer */}
      <MenuDrawer open={menuOpen} setOpen={setMenuOpen} />
    </div>
  );
}
