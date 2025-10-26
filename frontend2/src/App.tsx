import './App.css'
import { PageProvider, usePage} from './contexts/PageContext'
import PhoneDemo from './phone-demo/index'
import SidePanel from './side-panel/SidePanel'

function App() {

  return (
    <PageProvider>
      <div className='bg-red-200 grid grid-cols-5 flex justify-center'>
        <div className='col-span-5 bg-blue-300 flex flex-col'>
          <PhoneDemo />
        </div>
      </div>
    </PageProvider>
  )
}

export default App
