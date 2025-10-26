import { usePage } from '@/contexts/PageContext'
import { ArrowLeft, ArrowRight, House, Send } from 'lucide-react'
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
import { motion, AnimatePresence } from 'framer-motion'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { useState, useEffect, useRef } from 'react'

type ChatProps = {
  startMessage: string
}

type ChatMessage = {
  id: number
  text: string
  sender: 'ai' | 'user'
}

const AIInsights = () => {
  const { currentPage } = usePage()

  switch (currentPage) {
    case 'ai-insights':
      return <AIInsightsMain />; // default create content screen
    case 'ai-insights/engagement':
      return <AIEngagementInsights />;
    case 'ai-insights/chat-with-insight':
      return <ChatWithInsight startMessage='' />;
    default:
      return <div>Page not found</div>;
  }
}

export default AIInsights

const AIInsightsMain = () => {
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

const AIEngagementInsights = ()=>{
  const { setCurrentPage } = usePage()
  const [currentSlide, setCurrentSlide] = useState(0)
  const [message, setMessage] = useState('')

 const slides = [
  {
    title: 'Reel Performance',
    text: 'Your latest reel XYZ was engaged 10% higher than last week. Consider posting more content like this to maintain high audience interaction.',
    action: 'View Reel Analytics'
  },
  {
    title: 'Content Ideas',
    text: 'Your recent content ideas showed a better click-through rate. Focus on topics that resonate most with your audience for higher reach.',
    action: 'Explore Content Ideas'
  },
  {
    title: 'Story Insights',
    text: 'Stories posted in the last week reached 15% more viewers. Schedule similar stories during peak hours to maximize impressions.',
    action: 'Plan Next Story'
  },
  {
    title: 'Engagement Trends',
    text: 'Comments and shares increased by 8% this month. Engage with your audience more via polls or Q&A to boost interaction further.',
    action: 'Engage Audience'
  },
  {
    title: 'Recommendation Boost',
    text: 'Content tagged with trending keywords had 12% higher reach. Use trending hashtags and keywords to improve discoverability.',
    action: 'Optimize Tags'
  }
]

  const nextSlide = () => setCurrentSlide((prev) => (prev + 1) % slides.length)
  const prevSlide = () => setCurrentSlide((prev) => (prev - 1 + slides.length) % slides.length)

  const handleSendMessage = () => {
    if (!message.trim()) return
    console.log('User message:', message)
    setMessage('')
    setCurrentPage('ai-insights/chat-with-insight')
  }

  // Auto-advance slides every 8 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % slides.length)
    }, 8000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="w-full h-full flex flex-col items-center justify-between text-white relative bg-black">
      {/* Progress Indicators */}
      <div className="flex justify-center items-end gap-2 mt-6 w-full px-4">
        {slides.map((_, idx) => (
          <div
            key={idx}
            className={`h-1 flex-1 rounded-full ${
              currentSlide === idx ? 'bg-blue-500' : 'bg-gray-700'
            }`}
          />
        ))}
      </div>

      {/* Slides */}
      <div className="w-full h-full flex items-center justify-center relative overflow-hidden px-5">
        {/* Navigation Arrows */}
        <div
          className="absolute left-4 top-1/2 transform -translate-y-1/2 cursor-pointer z-10"
          onClick={prevSlide}
        >
          <ArrowLeft size={24} />
        </div>
        <div
          className="absolute right-4 top-1/2 transform -translate-y-1/2 cursor-pointer z-10"
          onClick={nextSlide}
        >
          <ArrowRight size={24} />
        </div>

        {/* Slide Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={currentSlide}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.6 }}
            className="bg-gray-700 rounded-xl w-full h-[85%] flex flex-col items-center justify-center text-center px-6 py-8"
          >
            <h2 className="text-2xl font-bold mb-4">{slides[currentSlide].title}</h2>
            <p className="text-lg mb-6">{slides[currentSlide].text}</p>
            <Button
              onClick={() => console.log(`Action: ${slides[currentSlide].action}`)}
              className="bg-blue-500 hover:bg-blue-400"
            >
              {slides[currentSlide].action}
            </Button>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Chat / Ask Question */}
      <div className="w-full p-4 bg-gray-900 flex gap-2">
        <Input
          type="text"
          placeholder="Ask a question..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <button
          className="bg-blue-500 px-4 rounded-md hover:bg-blue-400 flex items-center justify-center"
          onClick={handleSendMessage}
        >
          <Send />
        </button>
      </div>
    </div>
  )
}

const ChatWithInsight = ({ startMessage }: ChatProps) => {
  const { setCurrentPage } = usePage()
  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: 1, text: startMessage, sender: 'ai' }
  ])
  const [input, setInput] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)

  const handleSend = () => {
    if (!input.trim()) return
    const newMessage: ChatMessage = {
      id: messages.length + 1,
      text: input,
      sender: 'user'
    }
    setMessages((prev) => [...prev, newMessage])
    setInput('')

    // Example: After user sends message, move to a placeholder page
  }

  // Auto scroll to bottom on new message
  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: 'smooth'
    })
  }, [messages])

  return (
    <div className="w-full h-full flex flex-col bg-gray-900 text-white">
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3 bg-gray-800">
        <button
          className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white"
          onClick={() => setCurrentPage('home')}
        >
          <House />
        </button>
        <div className="text-md font-bold ml-3">AI Insights Chat</div>
      </div>

      {/* Chat Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-3"
      >
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`max-w-[70%] p-3 rounded-lg break-words ${
              msg.sender === 'ai' ? 'bg-blue-600 self-start' : 'bg-gray-700 self-end'
            }`}
          >
            {msg.text}
          </div>
        ))}
      </div>

      {/* Input Box */}
      <div className="p-4 flex gap-2 bg-gray-800">
        <Input
          type="text"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1"
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        />
        <Button
          onClick={handleSend}
          className="bg-blue-500 hover:bg-blue-400 px-4 flex items-center justify-center"
        >
          <Send />
        </Button>
      </div>
    </div>
  )
}