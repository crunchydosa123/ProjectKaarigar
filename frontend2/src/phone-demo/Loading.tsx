import React from 'react';

const Loading = () => {
  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col items-center justify-center"
      style={{ backgroundImage: "url('/white_bg.png')" }}
    >
      {/* Logo */}
      <div className="w-16 h-16 bg-cover bg-center rounded-full mb-4" style={{ backgroundImage: "url('/logo.png')" }}></div>
      
      {/* Loading text */}
      <div className="text-lg font-bold text-gray-700 mb-2">Project Kaarigar</div>
      <div className="text-sm text-gray-500">Loading...</div>
      
      {/* Simple loading spinner */}
      <div className="mt-4 w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
    </div>
  );
};

export default Loading;
