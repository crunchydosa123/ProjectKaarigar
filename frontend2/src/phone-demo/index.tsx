import { usePage } from '@/contexts/PageContext';
import Homepage from './Homepage';
import Onboarding from './Onboarding';
import PhoneLayout from './layout';
import CreateContent from './CreateContent';
import CreateLogo from './CreateLogo';
import CreateVideo from './CreateVideo';
import CreateVideo2 from './CreateVideo2';
import Login from './Login';
import Signup from './Signup';
import Loading from './Loading';
import AddProduct from './AddProduct';
import AICameraman from './AICameraman';
import Onboarding2 from './Onboarding2';
import ProfilePage from './ProfilePage';
import ViewProfile from './ViewProfile';
import AIInsights from './AIInsights';
import AIInsights2 from './AIInsights2';
import ChatWithInsight from './ChatWithInsight';


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

      {currentPage === "ai-insights" && <AIInsights />}
      {currentPage === "ai-insights/engagement" && <AIInsights2 />}
      {currentPage === "ai-insights/chat-with-insight" && <ChatWithInsight startMessage='' />}

      {/*Create Content Routes*/}
      {currentPage === "create-content" && <CreateContent />}
      {currentPage === "create-content/logos" && <CreateLogo />}
      {currentPage === "create-content/videos" && <CreateVideo />}
      {currentPage === "create-content/videos2" && <CreateVideo2 />}

      {/*Add Product Routes*/}
      {currentPage === "add-product" && <AddProduct />}
      {currentPage === "add-product/ai-cameraman" && <AICameraman />}
    </PhoneLayout>
  )
}

export default PhoneDemo
