import { PageProvider } from './contexts/PageContext'
import PhoneDemo from './phone-demo/index'

function App() {
  return (
    <PageProvider>
      <div className="bg-blue-300 grid grid-cols-5 min-h-screen">
        {/* Left Section */}
        <div className="bg-blue-300 flex col-span-3 w-full flex-col items-end">
          <PhoneDemo />
        </div>

        {/* Right Section */}
        <div className="flex flex-col col-span-2 py-10 px-5">
          <div className="text-2xl font-bold mb-3">
            Kaarigar Demo Portal
          </div>
          <p className="text-gray-700 mb-4">
            This page is part of the <strong>Project Kaarigar Hackathon Project</strong>.  
            It's a safe demo interface — no real credentials are requested, 
            stored, or transmitted.
          </p>

          {/* Project description */}
          <div className="text-xl font-semibold mb-3">About the Project</div>
          <p className="text-gray-600 mb-4">
            Kaarigar is an initiative to enable smarter digital tools for local artisans 
            and small businesses. This portal demonstrates the UI experience and 
            interactive features designed for accessibility and simplicity.
          </p>

          {/* Footer disclaimer */}
          <p className="text-xs text-gray-500 mt-8 text-center">
            © 2025 Project Kaarigar Hackathon Demo — built for educational purposes only.
          </p>
        </div>
      </div>
    </PageProvider>
  )
}

export default App
