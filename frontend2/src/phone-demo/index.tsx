import { usePage } from '@/contexts/PageContext';
import Homepage from './Homepage';
import Onboarding from './Onboarding';
import PhoneLayout from './layout';
import CreateContent from './CreateContent';
import CreateLogo from './CreateLogo';
import CreateVideo from './CreateVideo';
import CreateVideo2 from './CreateVideo2';


const PhoneDemo = () => {
  const { currentPage } = usePage();
  console.log(currentPage)

  return (
    <PhoneLayout>
      
      {currentPage === "home" && <Homepage /> }
      {currentPage === "onboarding" && <Onboarding />}

      {/*Create Content Routes*/}
      {currentPage === "create-content" && <CreateContent />}
      {currentPage === "create-content/logos" && <CreateLogo />}
      {currentPage === "create-content/videos" && <CreateVideo />}
      {currentPage === "create-content/videos2" && <CreateVideo2 />}
    </PhoneLayout>
  )
}

export default PhoneDemo
