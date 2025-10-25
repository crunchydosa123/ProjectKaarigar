import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { usePage } from '@/contexts/PageContext';
import { House, Image, GalleryVertical, Camera, ArrowRight } from 'lucide-react';

const AddProduct = () => {
  const { setCurrentPage } = usePage();
  const [selected, setSelected] = useState<string | null>(null);

  const handleSelect = (option: string) => {
    setSelected(option);
  };

  const handleNext = () => {
    if (!selected) return; // Prevent navigation if nothing is selected
    switch (selected) {
      case 'google':
        setCurrentPage('add-product/google-photos');
        break;
      case 'device':
        setCurrentPage('add-product/import-device');
        break;
      case 'ai':
        setCurrentPage('add-product/ai-cameraman');
        break;
      default:
        setCurrentPage('add-product');
    }
  };

  const isSelected = (option: string) => selected === option;

  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
      style={{ backgroundImage: "url('/white_bg.png')" }}
    >
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3">
        <button
          className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white"
          onClick={() => setCurrentPage('home')}
        >
          <House />
        </button>
        <div className="text-md font-bold ml-3">Add your Product to Kaarigar</div>
      </div>

      {/* Form */}
      <div className="p-3">
        <Label className="my-1">Name of Product</Label>
        <Input placeholder="for eg: Pashmina Shawl" />

        <div className="mt-4">
          <Label className="my-1">Choose a way to import product media</Label>
          <div className="flex justify-center gap-2 items-center">
            <Button
              variant={isSelected('google') ? 'default' : 'outline'}
              className="w-1/2 h-20 flex flex-col items-center justify-center gap-2"
              onClick={() => handleSelect('google')}
            >
              <Image className="h-5 w-5" />
              <span>Google Photos</span>
            </Button>

            <Button
              variant={isSelected('device') ? 'default' : 'outline'}
              className="w-1/2 h-20 flex flex-col items-center justify-center gap-2"
              onClick={() => handleSelect('device')}
            >
              <GalleryVertical className="h-5 w-5" />
              <span>Device Gallery</span>
            </Button>
          </div>

          <div className="flex justify-center items-center my-1 text-gray-600">or</div>

          <Button
            variant={isSelected('ai') ? 'default' : 'outline'}
            className="w-full h-20 flex flex-col justify-center items-center gap-2"
            onClick={() => handleSelect('ai')}
          >
            <Camera className="h-5 w-5" />
            <span>Click Photos now with AI Assistance</span>
          </Button>
        </div>

        <Button
          variant={selected ? 'default' : 'outline'}
          className={`mt-10 w-full flex justify-center items-center gap-2 ${!selected ? 'opacity-50 cursor-not-allowed' : ''}`}
          onClick={handleNext}
          disabled={!selected}
        >
          Next <ArrowRight />
        </Button>
      </div>
    </div>
  );
};

export default AddProduct;
