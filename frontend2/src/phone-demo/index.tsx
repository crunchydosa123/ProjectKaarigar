import { usePage } from '@/contexts/PageContext';
import Homepage from './Homepage';
import Onboarding from './Onboarding';
import PhoneLayout from './layout';
import CreateContent from './CreateContent';
import Login from './Login';
import Signup from './Signup';
import Loading from './Loading';
import AddProduct from './AddProduct';
import AICameraman from './AICameraman';
import Onboarding2 from './Onboarding2';
import ProfilePage from './ProfilePage';
import ViewProfile from './ViewProfile';
import AIInsights from './AIInsights';
import EditVideo from './EditVideo';
import EditContent from './EditContent';
import UploadMedia from './UploadMedia';
import ListProduct from './ListProducts';
import ListProducts from './ListProducts';
import ProductDetail from './ProductDetail';
import YouTubeShorts from './YouTubeShorts';
import AmazonListing from './AmazonListing';
import FlipkartListing from './FlipkartListing';
import MyntraListing from './MyntraListing';
import MarketplaceListings from './MarketplaceListings';


const PhoneDemo = () => {
  const { currentPage, loading } = usePage();
  console.log('Current page:', currentPage, 'Loading:', loading);

  // Show loading screen while checking authentication
  if (loading) {
    return (
      <PhoneLayout>
        <Loading />
      </PhoneLayout>
    );
  }

  return (
    <PhoneLayout>
      {/* Authentication Routes */}
      {currentPage === "login" && <Login />}
      {currentPage === "signup" && <Signup />}
      
      {/* Main App Routes */}
      {currentPage === "home" && <Homepage />}
      {currentPage === "profile" && <ViewProfile />}

      {currentPage === "onboarding" && <Onboarding />}
      {currentPage === "onboarding/details" && <Onboarding2 />}
      {currentPage === "onboarding/profile" && <ProfilePage />}

      {/*AI Insights Routes*/}
      {currentPage.startsWith("ai-insights") ? <AIInsights /> : null}

      {/*Create Content Routes*/}
      {currentPage.startsWith("create-content") ? <CreateContent /> : null}

      {currentPage.startsWith("edit-content") ? <EditContent /> : null}

      {/*Add Product Routes*/}
      {currentPage === "add-product" && <AddProduct />}
      {currentPage === "add-product/ai-cameraman" && <AICameraman />}

      {currentPage === "upload-media" && <UploadMedia />}

      {currentPage.startsWith("list-products") ? <ListProducts /> : null}
      
      {currentPage === "product-detail" && <ProductDetail />}
      
      {currentPage === "youtube-shorts" && <YouTubeShorts />}
      
      {currentPage === "marketplace-listings" && <MarketplaceListings />}
      {currentPage === "amazon-listing" && <AmazonListing />}
      {currentPage === "flipkart-listing" && <FlipkartListing />}
      {currentPage === "myntra-listing" && <MyntraListing />}
    </PhoneLayout>
  )
}

export default PhoneDemo
