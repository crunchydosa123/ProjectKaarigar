import { useState } from 'react'
import './App.css'
import { Button } from './components/ui/button'
import { Label } from './components/ui/label'
import { PageProvider } from './contexts/PageContext'
import PhoneDemo from './phone-demo/index'
import SidePanel from './side-panel/SidePanel'
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
          <div className="text-2xl font-bold mb-3">Additional Links for your reference</div>

          {/* Button 1 */}
          <button
            onClick={() =>
              window.open('https://www.youtube.com/watch?v=dQw4w9WgXcQ', '_blank')
            }
            className="bg-white rounded-md p-3 flex justify-start items-center gap-2 my-1 hover:shadow-md transition"
          >
            <img
              src="https://upload.wikimedia.org/wikipedia/commons/0/09/YouTube_full-color_icon_%282017%29.svg"
              alt="YouTube"
              className="w-6 h-6"
            />
            <div className="flex-col text-left">
              <div className="font-medium">Complete Walkthrough</div>
              <div className="text-xs text-gray-500">YouTube</div>
            </div>
          </button>

          {/* Button 2 */}
          <button
            onClick={() =>
              window.open('https://www.youtube.com/watch?v=ysz5S6PUM-U', '_blank')
            }
            className="bg-white rounded-md p-3 flex justify-start items-center gap-2 my-1 hover:shadow-md transition"
          >
            <img
              src="https://upload.wikimedia.org/wikipedia/commons/0/09/YouTube_full-color_icon_%282017%29.svg"
              alt="YouTube"
              className="w-6 h-6"
            />
            <div className="flex-col text-left">
              <div className="font-medium">See how WhatsApp messages are received</div>
              <div className="text-xs text-gray-500">YouTube</div>
            </div>
          </button>

          {/* Fallback Logins */}
          <div className="text-xl mt-16 font-semibold">
            In case of any failure, use any one of these fallback login credentials
          </div>

          <div className="grid grid-cols-2 w-full gap-4">
            {/* First Account */}
            <div className="bg-white p-6 my-3 rounded-xl shadow-md border border-gray-200">
              <h2 className="text-lg font-semibold text-gray-800 mb-1">Account Details</h2>
              <div className="mb-4 text-sm text-gray-500">(Try this first)</div>

              <div className="space-y-4">
                <div>
                  <Label className="text-gray-600 text-sm">Email</Label>
                  <div className="text-gray-900 font-medium mt-1">
                    surajchavan99886@gmail.com
                  </div>
                </div>

                <div>
                  <Label className="text-gray-600 text-sm">Password (Click to reveal)</Label>
                  <div className="flex items-center justify-between mt-1 bg-gray-50 px-3 py-2 rounded-md border border-gray-200">
                    <span className="text-gray-900 font-medium select-none">
                      {showPassword1 ? '123456' : '••••••'}
                    </span>
                    <button
                      type="button"
                      onClick={() => setShowPassword1(!showPassword1)}
                      className="text-gray-500 hover:text-gray-700 transition"
                    >
                      {showPassword1 ?<><EyeOff size={18} />Hide </> : <><Eye size={18} />Reveal</>}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Second Account */}
            <div className="bg-white p-6 my-3 rounded-xl shadow-md border border-gray-200">
              <h2 className="text-lg font-semibold text-gray-800 mb-4">Account Details</h2>

              <div className="space-y-4">
                <div>
                  <Label className="text-gray-600 text-sm">Email</Label>
                  <div className="text-gray-900 font-medium mt-1">raju.deo@gmail.com</div>
                </div>

                <div>
                  <Label className="text-gray-600 text-sm">Password (Click to reveal)</Label>
                  <div className="flex items-center justify-between mt-1 bg-gray-50 px-3 py-2 rounded-md border border-gray-200">
                    <span className="text-gray-900 font-medium select-none">
                      {showPassword ? '123456' : '••••••'}
                    </span>
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="text-gray-500 hover:text-gray-700 transition"
                    >
                      {showPassword ?<><EyeOff size={18} />Hide </> : <><Eye size={18} />Reveal</>}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </PageProvider>
  )
}

export default App
