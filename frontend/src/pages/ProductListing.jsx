import React, { useState, useRef } from "react";
import { Search, Upload, Plus, X } from "lucide-react";

export default function MobileProductListings() {
  const [products, setProducts] = useState([]);
  const [query, setQuery] = useState("");
  const [detail, setDetail] = useState(null);

  // Add-product form state
  const [pName, setPName] = useState("");
  const [pPrice, setPPrice] = useState("");
  const [pShort, setPShort] = useState("");
  const [pImageFile, setPImageFile] = useState(null);
  const [pImagePreview, setPImagePreview] = useState("");
  const [addSheetOpen, setAddSheetOpen] = useState(false);
  const imageInputRef = useRef(null);

  const handleImageChange = (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    setPImageFile(file);
    const url = URL.createObjectURL(file);
    setPImagePreview(url);
  };

  const handleAddProductSubmit = (e) => {
    e.preventDefault();
    if (!pName.trim() || !pPrice || !pShort.trim()) {
      alert("Please enter name, price and short description.");
      return;
    }

    const newProd = {
      id: Date.now(),
      name: pName.trim(),
      price: Number(pPrice),
      short: pShort.trim(),
      image: pImagePreview || "https://picsum.photos/seed/default/800/600",
    };

    setProducts((prev) => [newProd, ...prev]);

    // reset but don’t revoke blob immediately (avoid ERR_FILE_NOT_FOUND)
    setPName("");
    setPPrice("");
    setPShort("");
    setPImageFile(null);
    setPImagePreview("");
    setAddSheetOpen(false);
  };

  const filtered = products.filter(
    (p) =>
      p.name.toLowerCase().includes(query.toLowerCase()) ||
      p.short.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white relative p-4">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <button
          className="p-2 rounded-lg bg-white shadow-md"
          onClick={() => console.log("menu")}
        >
          <svg
            className="w-5 h-5 text-gray-700"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 6h16M4 12h16M4 18h16"
            />
          </svg>
        </button>

        <div className="flex-1 relative">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search products"
            className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-white shadow-sm focus:outline-none"
          />
          <Search className="absolute right-3 top-3 w-5 h-5 text-gray-400" />
        </div>

        <button
          onClick={() => setAddSheetOpen(true)}
          className="ml-2 p-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-md"
          aria-label="Add product"
        >
          <Plus className="w-5 h-5" />
        </button>
      </div>

      {/* Product grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {filtered.length === 0 ? (
          <div className="col-span-full text-center text-gray-500 py-12">
            No products — tap + to add one.
          </div>
        ) : (
          filtered.map((p) => (
            <article
              key={p.id}
              className="bg-white rounded-2xl shadow-sm overflow-hidden"
            >
              <button
                className="w-full block text-left"
                onClick={() => setDetail(p)}
              >
                <div className="w-full h-44 bg-gray-100 overflow-hidden">
                  <img
                    src={p.image}
                    alt={p.name}
                    className="w-full h-full object-cover"
                  />
                </div>

                <div className="p-3">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="text-sm font-semibold text-gray-800">
                      {p.name}
                    </h3>
                    <div className="text-sm font-semibold">₹{p.price}</div>
                  </div>

                  <p className="text-xs text-gray-500 mb-2 truncate">
                    {p.short}
                  </p>
                </div>
              </button>
            </article>
          ))
        )}
      </div>

      {/* Add Product sheet */}
      <div
        className={`fixed left-0 right-0 bottom-0 z-60 transition-transform duration-300 ${
          addSheetOpen ? "translate-y-0" : "translate-y-full"
        }`}
        aria-hidden={!addSheetOpen}
      >
        <div className="max-w-xl mx-auto bg-white/98 backdrop-blur-xl rounded-t-3xl shadow-2xl p-4 text-black">
          <div className="flex items-center justify-between mb-3">
            <div className="text-lg font-semibold">Add Product</div>
            <button
              onClick={() => setAddSheetOpen(false)}
              className="p-2 rounded-lg"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <form onSubmit={handleAddProductSubmit} className="space-y-3">
            <div>
              <label className="text-sm font-medium">Photo</label>
              <div className="mt-2 flex items-center gap-3">
                <div className="w-20 h-20 bg-gray-100 rounded-xl overflow-hidden flex items-center justify-center">
                  {pImagePreview ? (
                    <img
                      src={pImagePreview}
                      alt="preview"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <Upload className="w-7 h-7 text-gray-400" />
                  )}
                </div>

                <div className="flex-1">
                  <input
                    ref={imageInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleImageChange}
                    className="hidden"
                    id="add-photo"
                  />
                  <label
                    htmlFor="add-photo"
                    className="px-3 py-2 rounded-lg bg-white border border-gray-200 cursor-pointer inline-block"
                  >
                    Choose photo
                  </label>
                  {pImagePreview && (
                    <button
                      type="button"
                      onClick={() => {
                        setPImagePreview("");
                        setPImageFile(null);
                      }}
                      className="ml-2 px-3 py-2 rounded-lg bg-gray-100"
                    >
                      Remove
                    </button>
                  )}
                </div>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium">Name</label>
              <input
                value={pName}
                onChange={(e) => setPName(e.target.value)}
                className="w-full mt-2 px-3 py-2 rounded-lg border border-gray-200"
                placeholder="Product name"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Price (₹)</label>
              <input
                value={pPrice}
                onChange={(e) => setPPrice(e.target.value)}
                type="number"
                className="w-full mt-2 px-3 py-2 rounded-lg border border-gray-200"
                placeholder="e.g. 2499"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Short description</label>
              <input
                value={pShort}
                onChange={(e) => setPShort(e.target.value)}
                className="w-full mt-2 px-3 py-2 rounded-lg border border-gray-200"
                placeholder="One-liner for list view"
              />
            </div>

            <div className="flex items-center justify-between">
              <button
                type="button"
                onClick={() => {
                  setPName("");
                  setPPrice("");
                  setPShort("");
                  setPImagePreview("");
                  setPImageFile(null);
                  setAddSheetOpen(false);
                }}
                className="px-4 py-2 rounded-lg bg-gray-100"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded-lg bg-purple-600 text-white"
              >
                Add product
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Product detail slide-up */}
      {detail && (
        <div className="fixed inset-0 z-70 flex items-end">
          <div
            onClick={() => setDetail(null)}
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
          />
          <div className="relative w-full max-w-xl mx-auto bg-white rounded-t-3xl p-4 shadow-2xl z-70">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h2 className="text-lg font-semibold">{detail.name}</h2>
                <div className="text-sm text-gray-500">₹{detail.price}</div>
              </div>
              <button
                onClick={() => setDetail(null)}
                className="p-2 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="w-full h-56 bg-gray-100 mb-3 overflow-hidden rounded-xl">
              <img
                src={detail.image}
                alt={detail.name}
                className="w-full h-full object-cover"
              />
            </div>

            <p className="text-sm text-gray-700 mb-3">{detail.short}</p>
          </div>
        </div>
      )}
    </div>
  );
}
