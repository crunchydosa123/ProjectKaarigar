export default function MenuDrawer({ open, onClose }) {
  if (!open) return null;

  return (
    <>
      <div
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
      ></div>
      <div className="fixed inset-y-0 left-0 z-50 w-80 bg-gradient-to-br from-purple-100 via-blue-50 to-pink-100 shadow-xl transform translate-x-0 transition-transform duration-300 ease-in-out overflow-y-auto rounded-r-3xl">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-bold text-gray-900 headline">Menu</h3>
            <button
              onClick={onClose}
              className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center hover:bg-gray-300 transition-colors"
            >
              <span className="text-gray-600 text-lg">×</span>
            </button>
          </div>

          <ul className="space-y-3">
            <li className="p-3 bg-white/80 backdrop-blur-sm rounded-2xl text-gray-900 text-sm border border-white/30">User Profile</li>
            <li className="p-3 bg-white/80 backdrop-blur-sm rounded-2xl text-gray-900 text-sm border border-white/30">Video Generation</li>
            <li className="p-3 bg-white/80 backdrop-blur-sm rounded-2xl text-gray-900 text-sm border border-white/30">Video Editor</li>
            <li className="p-3 bg-white/80 backdrop-blur-sm rounded-2xl text-gray-900 text-sm border border-white/30">Image Generation</li>
            <li className="p-3 bg-white/80 backdrop-blur-sm rounded-2xl text-gray-900 text-sm border border-white/30">Image Editor</li>
          </ul>
        </div>
      </div>
    </>
  );
}
