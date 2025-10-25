import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { usePage } from '@/contexts/PageContext'
import { Facebook, House, Instagram, Twitter } from 'lucide-react';

const ProfilePage = () => {
  const { setCurrentPage } = usePage();
  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
      style={{ backgroundImage: "url('/white_bg.png')" }}
    >
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3">
        <button className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white" onClick={() => setCurrentPage('home')}><House /></button>
        <div className="text-md font-bold ml-3">Your Profile</div>
      </div>

      <div className='px-4 mb-5'>
        <div className='flex flex-col justify-center items-center rounded-md'>
          <img src='ai_gen_logo.jpeg' className='h-30 w-30 rounded-lg' />
          <Label className='mt-2'>Your Brand Logo</Label>
        </div>

        <div className='my-4'>
          <Label className='mb-1'>Your Brand's Name</Label>
          <Input type='text' value={'BackendWallah'} className='text-sm'></Input>
        </div>

        <div className=''>
          <Label className='mb-1'>Your Name</Label>
          <Input type='text' value={'Suraj Backendwala'} className='text-sm'></Input>
        </div>

        <div className='my-4'>
          <Label className='mb-1'>Your Email</Label>
          <Input type='text' value={'suraj@gmail.com'} className='text-sm'></Input>
        </div>

        <div className='my-4'>
          <Label className='mb-1'>Occupation</Label>
          <Input type='text' value={'Khandani Backend Dev'} className='text-sm'></Input>
        </div>

        <div className='my-4 '>
          <Label className='mb-1'>Social Media Links</Label>

          <div className='flex flex-col gap-2'>
            <div className='flex justify-start items-center gap-1'>
              <Instagram />
              <Input type='text' value={'@suraj12_12'} className='text-sm'></Input>
            </div>
            <div className='flex justify-start items-center gap-1'>
              <Facebook />
              <Input type='text' value={'@suraj12_12'} className='text-sm'></Input>
            </div>
            <div className='flex justify-start items-center gap-1'>
              <Twitter />
              <Input type='text' value={'@suraj12_12'} className='text-sm'></Input>
            </div>
          </div>
        </div>

        <Button className='w-full mt-3' onClick={() => setCurrentPage('home')}>Save Profile</Button>
      </div>
    </div>

  )
}

export default ProfilePage