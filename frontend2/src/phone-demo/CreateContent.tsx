import { Button } from '@/components/ui/button';
import { ButtonGroup } from '@/components/ui/button-group';
import { usePage } from '@/contexts/PageContext'
import { House } from 'lucide-react';
import { useState } from 'react';

const CreateContent = () => {
  const { setCurrentPage } = usePage();
  const [activeTab, setActiveTab] = useState<String>();
  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
      style={{ backgroundImage: "url('/white_bg.png')" }}
    >
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3">
        <button className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white" onClick={() => setCurrentPage('home')}><House /></button>
        <div className="text-md font-bold ml-3">Create Content with AI</div>
      </div>

      <div className='w-full px-4 py-2 text-xs flex flex-col gap-1'>
        <button className='w-full p-2 text-left font-semibold rounded-md bg-yellow-400' onClick={()=> setCurrentPage('create-content/logos')}>Generate Branding (Logos)</button>
        <button className='w-full p-2 text-left font-semibold rounded-md bg-red-400' onClick={()=> setCurrentPage('create-content/videos')}>Generate Videos</button>
        <button className='w-full p-2 text-left font-semibold rounded-md bg-green-400'>Generate Images</button>
      </div>

      <div className='w-full flex flex-col px-5 mt-2'>
        <div className='text-xs font-bold mb-2'>See your previously generated content</div>
        <div className='flex justify-center items-center w-full'>
          <ButtonGroup className='w-full'>
            <Button
              variant="outline"
              onClick={()=> setActiveTab('Logos')}
              className={`text-xs p-2 w-1/3 ${activeTab === 'Logos' ? 'bg-gray-400 text-white' : ''}`}>
              Logos
            </Button>    
            <Button
              variant="outline"
              onClick={()=> setActiveTab('Videos')}
              className={`text-xs p-2 w-1/3 ${activeTab === 'Videos' ? 'bg-gray-400 text-white' : ''}`}>
              Videos
            </Button>    
            <Button
              variant="outline"
              onClick={()=> setActiveTab('Images')}
              className={`text-xs p-2 w-1/3 ${activeTab === 'Images' ? 'bg-gray-400 text-white' : ''}`}>
              Images
            </Button>          
            </ButtonGroup>
        </div>
      </div>
    </div>
  )
}

export default CreateContent