import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { usePage } from '@/contexts/PageContext'
import { House, Sparkle, Upload } from 'lucide-react';


const Onboarding2 = () => {
  const {setCurrentPage} = usePage();

  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
      style={{ backgroundImage: "url('/white_bg.png')" }}
    >
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3">
        <button className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white" onClick={()=>setCurrentPage('home')}><House /></button>
        <div className="text-md font-bold ml-3">Conversational Onboarding</div>
      </div>

      <div className=''>
        <Label className='p-4'>Add/Create a logo for your brand</Label>
        <div className='mx-5 flex justify-center gap-2 items-center'>
          <Button variant='outline' className='w-1/2 flex flex-col h-30'>
            <Upload/><div>Upload a Logo</div></Button>

          <Button variant='outline' className='w-1/2 flex flex-col h-30'>
            <Sparkle /><div>Create a logo with AI</div>
          </Button>
        </div>
      </div>
    </div>
  )
}

export default Onboarding2