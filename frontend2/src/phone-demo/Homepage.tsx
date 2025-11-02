import { useEffect, useState } from 'react';
import { Lightbulb, Store, Upload, User } from 'lucide-react';
import { Camera } from 'lucide-react';
import { Megaphone } from 'lucide-react';
import { LogOut } from 'lucide-react';
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { usePage } from '@/contexts/PageContext';
import { productAPI } from '@/lib/api';
import type { ProductItem } from '@/lib/api';

const Homepage = () => {
  const { setCurrentPage, user, logout, setSelectedProductId } = usePage();
  
  const [products, setProducts] = useState<ProductItem[]>([]);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const resp = await productAPI.list();
        if (resp && resp.success && mounted) {
          setProducts(resp.products || []);
        }
      } catch (err) {
        console.error('Failed to load products:', err);
      }
    };
    load();
    return () => {
      mounted = false;
    };
  }, []);
  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col p-3"
      style={{ backgroundImage: "url('/homepage_bg.png')" }}
    >

      <div className='h-8 w-full mt-10 flex justify-between items-center'>
        <div className='flex items-center'>
          <div className="w-8 h-8 bg-cover bg-center" style={{ backgroundImage: "url('/logo.png')" }} ></div>
          <div className='flex flex-col justify-start mx-2'>
            <div className='text-sm font-bold'>Project Kaarigar</div>
            <div className='text-xs'>CyberWardens for GenAI Hackathon25</div>
          </div>
        </div>
        
        <div className='flex items-center gap-2'>
          <Button
            onClick={() => {
              logout();
            }}
            size="sm"
            variant="outline"
            className="bg-white/20 border-white/30 text-black hover:bg-white/30"
          >
            <LogOut className="w-3 h-3" />
          </Button>
        </div>
      </div>

      <div className='flex justify-between items-center mt-2'>
          
      {user && (
            <div className=' text-xs text-black'>
              Welcome, <b>{user.name}</b>
            </div>
          )}
          <Button
            onClick={() => {
              setCurrentPage('profile');
            }}
            size="sm"
            className="bg-purple-600 hover:bg-purple-700 text-white text-xs px-3 py-2 font-bold flex items-center gap-2 shadow-lg border-2 border-purple-800"
            style={{ minWidth: '80px', minHeight: '32px' }}
          >
            <User className="w-4 h-4" />
            Profile
          </Button>
          
      </div>    


      <div className='mt-2 w-full grid grid-cols-2 grid-row-2 gap-2'>
        <button className='bg-white rounded-md h-25 flex flex-col justify-between items-left' onClick={()=> setCurrentPage('onboarding')}>
          <div className='ml-2 mt-2 bg-[#EAC11D] w-12 h-12 rounded-lg flex items-center justify-center text-white'>
            <Megaphone />
          </div>
          <div className='text-xs font-bold m-2 text-left'>Build Your Brand Story</div>
        </button>

        <button className='bg-white rounded-md h-25 flex flex-col justify-between items-left' onClick={()=> setCurrentPage('list-products')}>
          <div className='ml-2 mt-2 bg-[#185FBC] w-12 h-12 rounded-lg flex items-center justify-center text-white'>
            <Store />
          </div>
          <div className='text-xs font-bold m-2 text-left'>List and Market your Products </div>
        </button>

        <button className='bg-white rounded-md h-25 flex flex-col justify-between items-left' onClick={()=> setCurrentPage('create-content')}>
          <div className='ml-2 mt-2 bg-[#00AF58] w-12 h-12 rounded-lg flex items-center justify-center text-white'>
            <Camera />
          </div>
          <div className='text-xs font-bold m-2 text-left'>Create Content with AI</div>
        </button>

        <button className='bg-white rounded-md h-25 flex flex-col justify-between items-left' onClick={() => setCurrentPage('ai-insights')}>
          <div className='ml-2 mt-2 bg-[#D25B79] w-12 h-12 rounded-lg flex items-center justify-center text-white'>
            <Lightbulb />
          </div>
          <div className='text-xs font-bold m-2 text-left'>Understand your Sales</div>
        </button>
      </div>

      <div className='mt-4 flex flex-col w-full'>

        <div className='flex justify-between items-center'>
          <div className='text-sm font-bold '>Your Products</div>
          <button className='py-1 px-2 my-1 text-xs font-semibold bg-white rounded-md' onClick={()=> setCurrentPage('list-products/add-products')}>+ Add Product</button>
        </div>
        

        <div className='flex space-x-3 overflow-x-auto pb-2 hide-scrollbar'>
          {products.map((product, index) => {
            const imageUrl = (product.image_urls && product.image_urls.length > 0)
              ? product.image_urls[0]
              : '/product1.png';

            return (
              <Card
                key={product.id || index}
                className='min-w-[160px] h-24 flex-shrink-0 relative p-0 overflow-hidden rounded-lg cursor-pointer'
                onClick={() => {
                  setSelectedProductId(product.id || null);
                  setCurrentPage('product-detail');
                }}
              >
                <div
                  className='absolute inset-0 bg-cover bg-center'
                  style={{ backgroundImage: `url(${imageUrl})` }}
                ></div>

                <div className='absolute inset-0 bg-black/30'></div>
                <div className='absolute bottom-2 left-2 text-white font-bold text-sm'>
                  {product.name}
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      <div className='mt-4 flex flex-col w-full gap-1'>
        <div className='flex justify-between items-center my-1'>
        <div className='text-sm font-bold mb-1'>Post Content</div>
        <Button
            onClick={()=> setCurrentPage('upload-media')}
            size="sm"
            className="bg-purple-600 hover:bg-purple-700 text-white text-xs px-3 py-2 font-bold flex items-center gap-2 shadow-lg border-2 border-purple-800"
            style={{ minWidth: '80px', minHeight: '32px' }}
          >
            <Upload className="w-4 h-4" />
            Upload 
          </Button> 
        </div>
        <button 
          className='bg-white rounded-sm h-10 flex justify-start p-2 w-full'
          onClick={()=> setCurrentPage('youtube-shorts')}
        >
          <div className="w-6 h-6 bg-cover bg-center mr-2" style={{ backgroundImage: "url('/youtube.png')" }} ></div>
          <div className='flex flex-col items-start justify-center'>
            <div className='text-sm font-bold text-left'>YouTube</div>
            <div className='text-xs text-left'>Videos, Shorts</div>
          </div>
        </button>

        <button className='bg-white rounded-sm h-10 flex justify-start p-2' onClick={()=> setCurrentPage('list-products/whatsapp-campaign')}>
          <div className="w-6 h-6 bg-cover bg-center mr-2 " style={{ backgroundImage: "url('/WhatsApp.webp')" }} ></div>
          <div className='flex flex-col items-start justify-center'>
            <div className='text-sm font-bold'>WhatsApp</div>
            <div className='text-xs'>Message Campaign</div>
          </div>
        </button>
      </div>

    </div>
  )
}

export default Homepage