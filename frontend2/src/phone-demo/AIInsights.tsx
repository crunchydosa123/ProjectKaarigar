import { usePage } from '@/contexts/PageContext'
import { House } from 'lucide-react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

const AIInsights = () => {
  const { setCurrentPage } = usePage()

  // Example data
  const inventoryData = [
    { month: 'Jan', stock: 120 },
    { month: 'Feb', stock: 140 },
    { month: 'Mar', stock: 100 },
    { month: 'Apr', stock: 160 },
    { month: 'May', stock: 180 },
  ]

  const financialData = [
    { month: 'Jan', revenue: 12000, expense: 8000 },
    { month: 'Feb', revenue: 15000, expense: 9000 },
    { month: 'Mar', revenue: 13000, expense: 8500 },
    { month: 'Apr', revenue: 17000, expense: 11000 },
    { month: 'May', revenue: 20000, expense: 13000 },
  ]

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
        <div className="text-md font-bold ml-3">AI Insights</div>
      </div>

      <div className="flex-col px-5">
        <button className="w-full my-1 border rounded-md py-1 px-2 text-left text-sm hover:bg-blue-50 transition" onClick={()=> setCurrentPage('ai-insights/engagement')}>
          Engagement with your content
        </button>
        <button className="w-full my-1 border rounded-md py-1 px-2 text-left text-sm hover:bg-blue-50 transition">
          Financials
        </button>
        <button className="w-full my-1 border rounded-md py-1 px-2 text-left text-sm hover:bg-blue-50 transition">
          Recent Trends
        </button>
      </div>

      {/* Graphs */}
      <div className="flex flex-col items-center mt-8 px-5 gap-8">
        {/* Inventory Chart */}
        <div className="w-full max-w-xl bg-white border rounded-xl p-4 shadow-sm">
          <h2 className="font-semibold text-gray-700 mb-2 text-center">Inventory Levels</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={inventoryData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="stock" fill="#3b82f6" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Financial Chart */}
        <div className="w-full max-w-xl bg-white border rounded-xl p-4 shadow-sm">
          <h2 className="font-semibold text-gray-700 mb-2 text-center">Financial Overview</h2>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={financialData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="revenue" stroke="#22c55e" strokeWidth={2} />
              <Line type="monotone" dataKey="expense" stroke="#ef4444" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

export default AIInsights
