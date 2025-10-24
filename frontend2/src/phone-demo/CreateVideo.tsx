import { usePage } from '@/contexts/PageContext'
import { Label } from "@/components/ui/label"
import {
  RadioGroup,
  RadioGroupItem,
} from "@/components/ui/radio-group"
import { ArrowRight, House } from 'lucide-react';
import { useState } from 'react'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from "@/components/ui/command"
import { Button } from '@/components/ui/button';


const CreateVideo = () => {
  const { setCurrentPage } = usePage();
  const [selectedProduct, setSelectedProduct] = useState<string | null>(null);
  const [useProductMedia, setUseProductMedia] = useState(false);

  const products = ["Product 1", "Product 2", "Product 3"];
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

      <div className='flex flex-col px-5 mt-1'>
        <div className='text-sm font-semibold'>Select the type of Video</div>
        <RadioGroup defaultValue="option-one" className='text-xs flex flex-col gap-1 mt-2'>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="option-one" id="option-one" />
            <Label htmlFor="option-one">Vertical 16:9 (Reels, Shorts)</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="option-two" id="option-two" />
            <Label htmlFor="option-two">Horizontal 9:16 (YouTube Ads)</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="option-three" id="option-three" />
            <Label htmlFor="option-two">Custom (Masti nahi rukni chahiye)</Label>
          </div>
        </RadioGroup>
      </div>

      <div className="flex flex-col px-5 mt-5">
        <div className="text-sm font-semibold mb-2">Select Product (optional)</div>

        {/* Command box */}
        <Command className="rounded-lg border shadow-sm w-full max-w-md bg-white">
          <CommandInput placeholder="Search for a product..." className="text-xs" />
          <CommandEmpty>No Products Found</CommandEmpty>

          <CommandGroup heading="Products">
            {products.map((product, idx) => (
              <CommandItem
                key={idx}
                onSelect={() => setSelectedProduct(product)}
                className={`cursor-pointer text-xs ${selectedProduct === product
                  ? "bg-blue-100 text-blue-700"
                  : "hover:bg-gray-100"
                  }`}
              >
                <span>{product}</span>
              </CommandItem>
            ))}
          </CommandGroup>
        </Command>

        {/* Show selected product */}
        {selectedProduct && (
          <div className="mt-3 flex flex-col items-center gap-2 text-sm w-full">
            <div className='w-full flex justify-start items-center gap-2'>
              <span className="text-gray-600">Selected:</span>
              <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-md font-medium">
                {selectedProduct}
              </span>
            </div>


            <div className="flex items-center gap-2 text-xs">
              <input
                id="useProductMedia"
                type="checkbox"
                checked={useProductMedia}
                onChange={(e) => setUseProductMedia(e.target.checked)}
                className="w-4 h-4 accent-blue-600 cursor-pointer"
              />
              <label
                htmlFor="useProductMedia"
                className="text-gray-700 cursor-pointer"
              >
                Use {selectedProduct}'s photos and videos to generate video
              </label>
            </div>
          </div>
        )}

        <Button variant={'outline'} className='mt-5' onClick={()=> setCurrentPage('create-content/videos2')}>Start Creating Video <ArrowRight /></Button>

      </div>
    </div>

  )
}

export default CreateVideo