import './App.css'
import { PageProvider} from './contexts/PageContext'
import PhoneDemo from './phone-demo/index'
import SidePanel from './side-panel/SidePanel'

function App() {

  return (
    <PageProvider>
      <div className='bg-red-200 grid grid-cols-5'>
        <div className='col-span-2 bg-blue-300 flex flex-col'>
          <div className='text-center mt-5 mb-2 text-2xl font-bold'>App Demo</div>
          <PhoneDemo />
        </div>

        <div className='bg-red-200 col-span-3'><SidePanel /></div>
      </div>
    </PageProvider>
  )
}

export default App
