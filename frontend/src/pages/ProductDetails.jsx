// src/pages/ProductDetail.jsx
import React, { useContext, useState } from "react";
import { ArrowLeft, Sparkles, Stars } from "lucide-react";
import { useParams, useNavigate } from "react-router-dom";
import { ProductContext } from "../context/ProductContext";

export default function ProductDetail() {
  const { id } = useParams();
  const { products } = useContext(ProductContext);
  const navigate = useNavigate();
  const [selectedImage, setSelectedImage] = useState(null);

  const detail = products.find((p) => p.id == id);

  if (!detail) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-100 via-blue-50 to-pink-100 flex items-center justify-center">
        <div className="text-center text-gray-800 text-lg font-medium">
          Product not found
        </div>
      </div>
    );
  }

  const optimized = detail.optimized || {};
  const images =
    detail.original?.uploaded_images?.map((p) =>
      p.startsWith("http") ? p : p
    ) || detail.images || [];
  const selected = selectedImage || images[0] || detail.image || "";

  const suggestedPrice =
    optimized.suggested_price ?? detail.optimized?.suggested_price ?? null;
  const originalPrice =
    detail.original?.price ?? detail.price ?? detail.original?.price;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-100 via-blue-50 to-pink-100 relative overflow-hidden flex flex-col">
      {/* Floating background blobs */}
      <div className="absolute top-10 left-10 transform -translate-x-1/2 w-72 h-72 bg-gradient-to-br from-purple-300 to-pink-300 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse md:transform-none" />
      <div className="absolute top-20 right-10 w-64 h-64 bg-gradient-to-br from-blue-300 to-purple-300 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse delay-1000 hidden md:block" />
      <div className="absolute bottom-10 left-1/2 w-80 h-80 bg-gradient-to-br from-pink-300 to-blue-300 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse delay-2000" />

      {/* Header */}
      <header className="relative z-10 p-4 pt-16">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-purple-400 to-pink-400 rounded-2xl mb-4 shadow-lg">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-purple-700 to-pink-600 bg-clip-text text-transparent">
            Product details
          </h1>
        </div>

        {/* Back button */}
        <button
          aria-label="Back"
          onClick={() => navigate("/product-listing")}
          className="absolute top-4 left-4 p-2 rounded-lg bg-white/40 backdrop-blur-sm border border-white/30 shadow hover:scale-95 transition-transform"
        >
          <ArrowLeft className="w-5 h-5 text-gray-800" />
        </button>
      </header>

      {/* Main content */}
      <main className="relative z-10 px-4 pb-12 flex-1 overflow-y-auto">
        <section className="max-w-3xl mx-auto space-y-10">
          {/* Image gallery */}
          <div className="flex flex-col items-center">
            {selected ? (
              <img
                src={selected}
                alt="product"
                className="w-full max-h-80 object-cover rounded-2xl shadow-lg"
                draggable={false}
              />
            ) : (
              <div className="w-full max-h-80 rounded-2xl bg-white/40 backdrop-blur-sm border border-white/30 flex items-center justify-center">
                <span className="text-gray-700">No image</span>
              </div>
            )}

            {images.length > 1 && (
              <div className="w-full mt-3">
                <div className="flex gap-3 overflow-x-auto py-1 px-1">
                  {images.map((url, idx) => (
                    <button
                      key={idx}
                      onClick={() => setSelectedImage(url)}
                      className={`flex-shrink-0 rounded-lg overflow-hidden border-2 ${
                        selected === url
                          ? "border-purple-600"
                          : "border-transparent"
                      }`}
                      aria-label={`Select image ${idx + 1}`}
                    >
                      <img
                        src={url}
                        alt={`thumb-${idx}`}
                        className="w-20 h-20 object-cover"
                        draggable={false}
                      />
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* AI suggested product name */}
          <div className="px-1">
            <h2 className="text-lg font-semibold text-purple-700 mb-2 flex items-center gap-2">
              <Stars className="w-5 h-5 text-purple-600" />
              AI suggested product name
            </h2>
            <p className="text-xl font-bold text-gray-900">
              {optimized.suggested_name ?? detail.name}
            </p>
          </div>

          {/* AI suggested price */}
          <div className="px-1">
            <h2 className="text-lg font-semibold text-purple-700 mb-2 flex items-center gap-2">
              <Stars className="w-5 h-5 text-purple-600" />
              AI suggested price
            </h2>
            <div className="text-2xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-purple-700 to-pink-600">
              ₹{suggestedPrice ?? originalPrice ?? "—"}
            </div>
          </div>

          {/* AI suggested description */}
          <div className="px-1">
            <h2 className="text-lg font-semibold text-purple-700 mb-2 flex items-center gap-2">
              <Stars className="w-5 h-5 text-purple-600" />
              AI suggested description
            </h2>
            <p className="text-sm text-gray-800 leading-relaxed">
              {optimized.suggested_description ??
                detail.original?.description ??
                detail.short ??
                "No description available."}
            </p>
          </div>

          {/* Product demo video */}
          {detail.video && (
            <div className="px-1">
              <h2 className="text-lg font-semibold text-purple-700 mb-2">
                Product demo video
              </h2>
              <video
                src={detail.video}
                controls
                className="w-full rounded-lg"
              />
            </div>
          )}

          {/* SEO tags */}
          {optimized.seo_tags && optimized.seo_tags.length > 0 && (
            <div className="px-1">
              <h2 className="text-lg font-semibold text-purple-700 mb-2 flex items-center gap-2">
                <Stars className="w-5 h-5 text-purple-600" />
                AI suggested SEO tags
              </h2>
              <div className="flex flex-wrap gap-2">
                {optimized.seo_tags.map((tag, i) => (
                  <span
                    key={i}
                    className="px-3 py-1 rounded-full text-xs font-medium bg-gradient-to-br from-purple-400 to-blue-400 text-white select-none"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
