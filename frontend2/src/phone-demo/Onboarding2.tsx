import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { usePage } from '@/contexts/PageContext'
import { Popover, PopoverContent, PopoverTrigger } from '@radix-ui/react-popover';
import { House, Sparkle, Upload } from 'lucide-react';
import { useState } from 'react';


const Onboarding2 = () => {
  const { setCurrentPage } = usePage();
  const [selectedLogo, setSelectedLogo] = useState<number | null>(null);


  const uploadedLogos = [
    "/ai_gen_logo.jpeg",
    "/ai_gen_logo2.jpeg",
    "/ai_gen_logo3.jpeg",
    "/ai_gen_logo4.jpeg",
  ];

  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
      style={{ backgroundImage: "url('/white_bg.png')" }}
    >
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3">
        <button className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white" onClick={() => setCurrentPage('home')}><House /></button>
        <div className="text-md font-bold ml-3">Conversational Onboarding</div>
      </div>

      <div className=''>
        <Label className='p-4'>Add/Create a logo for your brand</Label>
        <div className='mx-5 flex justify-center gap-2 items-center'>

          <div className="w-1/2">
            <Popover>
              <PopoverTrigger>
                <Button variant="outline" className="flex flex-col items-center h-30">
                  <Upload className="w-6 h-6 mb-1" />
                  <div>Upload a Logo</div>
                </Button>
              </PopoverTrigger>

              <PopoverContent className="w-72 p-2">
                <Card className="p-2">
                  <CardHeader>
                    <CardTitle>Your Photos</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-2">
                      {uploadedLogos.map((logo, idx) => (
                        <button
                          key={idx}
                          onClick={() => setSelectedLogo(idx)}
                          className={`border-2 rounded-md p-1 transition ${selectedLogo === idx
                              ? "border-blue-500"
                              : "border-gray-300 border-dashed"
                            }`}
                        >
                          <img src={logo} alt={`logo-${idx}`} className="w-full h-20 object-contain" />
                        </button>
                      ))}
                    </div>

                    {selectedLogo !== null && (
                      <div className="mt-2 flex justify-center">
                        <Button className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-1 rounded-md">
                          SELECT THIS LOGO
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </PopoverContent>
            </Popover>
          </div>


          <Button variant='outline' className='w-1/2 flex flex-col h-30' onClick={() => setCurrentPage('create-content/logos')}>
            <Sparkle /><div>Create a logo with AI</div>
          </Button>
        </div>
      </div>
    </div>
  )
}

export default Onboarding2