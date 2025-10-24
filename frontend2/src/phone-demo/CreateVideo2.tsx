import VideoEditorPreview from '@/components/custom/VideoEditorPreview';
import { usePage } from '@/contexts/PageContext'
import { House } from 'lucide-react';

const CreateVideo2 = () => {
  const { setCurrentPage } = usePage();
  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
      style={{ backgroundImage: "url('/white_bg.png')" }}
    >
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3">
        <button className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white" onClick={() => setCurrentPage('home')}><House /></button>
        <div className="text-md font-bold ml-3">Create Video with AI</div>
      </div>

      <div className="bg-[#1e1e1e] text-white  shadow-lg p-4 w-full max-w-2xl mx-auto">
        <VideoEditorPreview />
      </div>

    </div>
  )
}

export default CreateVideo2