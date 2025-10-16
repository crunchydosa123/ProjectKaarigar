import { usePage } from '@/contexts/PageContext';
import Homepage from './Homepage';
import Onboarding from './Onboarding';
import PhoneLayout from './layout';


const PhoneDemo = () => {
  const { currentPage } = usePage();
  console.log(currentPage)

  return (
    <PhoneLayout>
      
      {currentPage === "home" && <Homepage /> }
      {currentPage === "onboarding" && <Onboarding />}
    </PhoneLayout>
  )
}

export default PhoneDemo
