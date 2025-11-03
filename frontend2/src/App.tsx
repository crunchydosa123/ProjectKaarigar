import { useState } from 'react'
import './App.css'
import { Button } from './components/ui/button'
import { Label } from './components/ui/label'
import { PageProvider } from './contexts/PageContext'
import PhoneDemo from './phone-demo/index'
import { Eye, EyeOff } from 'lucide-react'

function App() {
  const [showPassword, setShowPassword] = useState(false)
  const [showPassword1, setShowPassword1] = useState(false)

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
            It’s a safe demo login interface — no real credentials are requested, 
            stored, or transmitted.
          </p>

          {/* Demo walkthrough buttons */}
          <div className="text-xl font-semibold mb-3">Demo Resources</div>

          <button
            onClick={() =>
              window.open('https://www.youtube.com/watch?v=eVoegX7q474', '_blank')
            }
            className="bg-white rounded-md p-3 flex justify-start items-center gap-2 my-1 hover:shadow-md transition"
          >
            <img
              src="https://upload.wikimedia.org/wikipedia/commons/0/09/YouTube_full-color_icon_%282017%29.svg"
              alt="YouTube"
              className="w-6 h-6"
            />
            <div className="flex-col text-left">
              <div className="font-medium">Complete Project Walkthrough</div>
              <div className="text-xs text-gray-500">YouTube</div>
            </div>
          </button>

          <button
            onClick={() =>
              window.open('https://www.youtube.com/watch?v=e7VUdxC5V8A', '_blank')
            }
            className="bg-white rounded-md p-3 flex justify-start items-center gap-2 my-1 hover:shadow-md transition"
          >
            <img
              src="https://upload.wikimedia.org/wikipedia/commons/0/09/YouTube_full-color_icon_%282017%29.svg"
              alt="YouTube"
              className="w-6 h-6"
            />
            <div className="flex-col text-left">
              <div className="font-medium">WhatsApp Integration Demo</div>
              <div className="text-xs text-gray-500">YouTube</div>
            </div>
          </button>

          {/* Demo login info */}
          <div className="text-xl mt-16 font-semibold">
            Demo Access (for reviewers)
          </div>
          <p className="text-sm text-gray-600 mb-4">
            Use these <strong>sample accounts</strong> for demonstration. These are not real users.
          </p>

          <div className="grid grid-cols-2 w-full gap-4">
            {/* First Account */}
            <div className="bg-white p-6 my-3 rounded-xl shadow-md border border-gray-200">
              <h2 className="text-lg font-semibold text-gray-800 mb-1">Sample Account A</h2>
              <div className="mb-4 text-sm text-gray-500">(Demo credentials)</div>

              <div className="space-y-4">
                <div>
                  <Label className="text-gray-600 text-sm">Email</Label>
                  <div className="text-gray-900 font-medium mt-1">
                    demo.userA@example.com
                  </div>
                </div>

                <div>
                  <Label className="text-gray-600 text-sm">Password (Click to reveal)</Label>
                  <div className="flex items-center justify-between mt-1 bg-gray-50 px-3 py-2 rounded-md border border-gray-200">
                    <span className="text-gray-900 font-medium select-none">
                      {showPassword1 ? 'demo123' : '••••••'}
                    </span>
                    <button
                      type="button"
                      onClick={() => setShowPassword1(!showPassword1)}
                      className="text-gray-500 hover:text-gray-700 transition"
                    >
                      {showPassword1 ? (
                        <>
                          <EyeOff size={18} /> Hide
                        </>
                      ) : (
                        <>
                          <Eye size={18} /> Reveal
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Second Account */}
            <div className="bg-white p-6 my-3 rounded-xl shadow-md border border-gray-200">
              <h2 className="text-lg font-semibold text-gray-800 mb-4">Sample Account B</h2>

              <div className="space-y-4">
                <div>
                  <Label className="text-gray-600 text-sm">Email</Label>
                  <div className="text-gray-900 font-medium mt-1">
                    demo.userB@example.com
                  </div>
                </div>

                <div>
                  <Label className="text-gray-600 text-sm">Password (Click to reveal)</Label>
                  <div className="flex items-center justify-between mt-1 bg-gray-50 px-3 py-2 rounded-md border border-gray-200">
                    <span className="text-gray-900 font-medium select-none">
                      {showPassword ? 'demo456' : '••••••'}
                    </span>
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="text-gray-500 hover:text-gray-700 transition"
                    >
                      {showPassword ? (
                        <>
                          <EyeOff size={18} /> Hide
                        </>
                      ) : (
                        <>
                          <Eye size={18} /> Reveal
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Footer disclaimer */}
          <p className="text-xs text-gray-500 mt-8 text-center">
            © 2025 Kaarigar Club Hackathon Demo — built for educational purposes only.
          </p>
        </div>
      </div>
    </PageProvider>
  )
}

export default App
