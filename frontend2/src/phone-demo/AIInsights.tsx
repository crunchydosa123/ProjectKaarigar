import { usePage } from '@/contexts/PageContext'
import { ArrowLeft, ArrowRight, House, Send, RefreshCw, ExternalLink, Loader2 } from 'lucide-react'
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
import { aiInsightsAPI, type AIInsight } from '@/lib/api'

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
    case 'ai-insights/insight-detail':
      return <InsightDetail />;
    case 'ai-insights/links':
      return <LinksPage />;
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

const AIEngagementInsights = () => {
  const { setCurrentPage } = usePage()
  const [insights, setInsights] = useState<AIInsight[]>([])
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [currentSlide, setCurrentSlide] = useState(0)

  // Load insights on mount
  useEffect(() => {
    loadInsights()
  }, [])

  // Auto-advance slides every 8 seconds (only if insights exist)
  useEffect(() => {
    if (insights.length === 0) return
    
    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % insights.length)
    }, 8000)
    return () => clearInterval(interval)
  }, [insights.length])

  const loadInsights = async () => {
    try {
      console.log('🔍 Loading AI insights...')
      setLoading(true)
      const response = await aiInsightsAPI.getInsights()
      console.log('📥 Insights response:', response)
      
      if (response.success && response.insights.length > 0) {
        console.log(`✅ Loaded ${response.insights.length} insights`)
        setInsights(response.insights)
      } else {
        console.log('ℹ️ No insights found - user needs to generate')
        setInsights([])
      }
    } catch (error: any) {
      console.error('❌ Error loading insights:', error)
      console.error('Error details:', {
        message: error.message,
        stack: error.stack
      })
      alert(`Error loading insights: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateLatest = async () => {
    try {
      console.log('\n' + '='.repeat(80))
      console.log('✨ Starting AI insights generation...')
      console.log('='.repeat(80))
      
      setGenerating(true)
      
      console.log('📡 Calling generateInsights API...')
      const response = await aiInsightsAPI.generateInsights()
      console.log('📥 Generation response:', response)
      
      if (response.success && response.insights) {
        console.log(`✅ Successfully generated ${response.insights.length} insights`)
        console.log('Insights preview:', response.insights.map((i: AIInsight) => ({
          title: i.title,
          hasImage: !!i.image_url,
          textLength: i.text.length
        })))
        
        setInsights(response.insights)
        setCurrentSlide(0) // Reset to first slide
        alert('✅ AI Insights generated successfully!')
      } else {
        console.error('❌ Generation failed - no insights in response')
        alert('Failed to generate insights')
      }
    } catch (error: any) {
      console.error('\n❌ Error generating insights:', error)
      console.error('Error details:', {
        message: error.message,
        stack: error.stack,
        name: error.name
      })
      alert(`Error generating insights: ${error.message}`)
    } finally {
      setGenerating(false)
      console.log('='.repeat(80) + '\n')
    }
  }

  const nextSlide = () => setCurrentSlide((prev) => (prev + 1) % insights.length)
  const prevSlide = () => setCurrentSlide((prev) => (prev - 1 + insights.length) % insights.length)

  const handleCardClick = () => {
    // Store current insight to session storage
    sessionStorage.setItem('selectedInsightIndex', currentSlide.toString())
    sessionStorage.setItem('selectedInsight', JSON.stringify(insights[currentSlide]))
    setCurrentPage('ai-insights/insight-detail')
  }

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-black">
        <Loader2 className="animate-spin text-blue-500" size={48} />
      </div>
    )
  }

  return (
    <div className="w-full h-full flex flex-col items-center justify-between text-white relative bg-black">
      {/* Header with buttons */}
      <div className="absolute top-4 left-4 right-4 flex justify-between items-center z-20">
        <Button
          onClick={() => setCurrentPage('ai-insights/links')}
          className="bg-gray-700 hover:bg-gray-600"
          size="sm"
        >
          <ExternalLink className="mr-1" size={16} />
          Helpful Links
        </Button>
        <Button
          onClick={handleGenerateLatest}
          disabled={generating}
          className="bg-blue-500 hover:bg-blue-400"
          size="sm"
        >
          {generating ? (
            <>
              <Loader2 className="animate-spin mr-1" size={16} />
              Generating...
            </>
          ) : (
            <>
              <RefreshCw className="mr-1" size={16} />
              Get Latest
            </>
          )}
        </Button>
      </div>

      {/* Content */}
      {insights.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center px-4 text-center">
          <h2 className="text-2xl font-bold mb-4">No AI Insights Yet</h2>
          <p className="text-gray-400 mb-6">
            Click "Get Latest" to generate personalized business insights based on your profile
          </p>
          <Button
            onClick={handleGenerateLatest}
            disabled={generating}
            className="bg-blue-500 hover:bg-blue-400"
          >
            {generating ? (
              <>
                <Loader2 className="animate-spin mr-2" size={20} />
                Generating AI Insights...
              </>
            ) : (
              'Generate AI Insights'
            )}
          </Button>
        </div>
      ) : (
        <>
          {/* Progress Indicators */}
          <div className="flex justify-center items-end gap-2 mt-6 w-full px-4 z-10">
            {insights.map((_, idx) => (
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
              className="absolute left-4 top-1/2 transform -translate-y-1/2 cursor-pointer z-20 bg-black/50 rounded-full p-2 hover:bg-black/70"
              onClick={(e) => {
                e.stopPropagation()
                prevSlide()
              }}
            >
              <ArrowLeft size={24} />
            </div>
            <div
              className="absolute right-4 top-1/2 transform -translate-y-1/2 cursor-pointer z-20 bg-black/50 rounded-full p-2 hover:bg-black/70"
              onClick={(e) => {
                e.stopPropagation()
                nextSlide()
              }}
            >
              <ArrowRight size={24} />
            </div>

            {/* Slide Content */}
            <AnimatePresence mode="wait">
              <motion.div
                key={currentSlide}
                initial={{ opacity: 0, x: 100 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -100 }}
                transition={{ duration: 0.5 }}
                onClick={handleCardClick}
                className="rounded-xl w-full h-[85%] flex flex-col items-center justify-end text-center relative overflow-hidden cursor-pointer"
              >
                {/* Background Image or Black */}
                {insights[currentSlide].image_url ? (
                  <img
                    src={insights[currentSlide].image_url}
                    alt={insights[currentSlide].title}
                    className="absolute inset-0 w-full h-full object-cover"
                  />
                ) : (
                  <div className="absolute inset-0 w-full h-full bg-black" />
                )}

                {/* Gradient Overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent" />

                {/* Title and Text Overlay */}
                <div className="relative z-10 px-6 pb-8 w-full">
                  <h2 className="text-2xl font-bold mb-4">{insights[currentSlide].title}</h2>
                  <p className="text-lg leading-relaxed line-clamp-4">
                    {insights[currentSlide].text}
                  </p>
                  <p className="text-sm text-gray-400 mt-4">Tap to read more</p>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
        </>
      )}
    </div>
  )
}

const InsightDetail = () => {
  const { setCurrentPage } = usePage()
  const [insight, setInsight] = useState<AIInsight | null>(null)

  useEffect(() => {
    // Load selected insight from session storage
    const storedInsight = sessionStorage.getItem('selectedInsight')
    if (storedInsight) {
      setInsight(JSON.parse(storedInsight))
    }
  }, [])

  if (!insight) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-900 text-white">
        <p>No insight selected</p>
      </div>
    )
  }

  return (
    <div className="w-full h-full flex flex-col bg-gray-900 text-white overflow-y-auto">
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3 bg-gray-800 sticky top-0 z-10">
        <button
          className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white"
          onClick={() => setCurrentPage('ai-insights/engagement')}
        >
          <ArrowLeft />
        </button>
        <div className="text-md font-bold ml-3">Insight Details</div>
      </div>

      {/* Image */}
      <div className="w-full">
        {insight.image_url ? (
          <img
            src={insight.image_url}
            alt={insight.title}
            className="w-full h-64 object-cover"
          />
        ) : (
          <div className="w-full h-64 bg-black" />
        )}
      </div>

      {/* Content */}
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">{insight.title}</h1>
        <p className="text-gray-300 leading-relaxed whitespace-pre-wrap">
          {insight.text}
        </p>
      </div>
    </div>
  )
}

const LinksPage = () => {
  const { setCurrentPage } = usePage()
  const [links, setLinks] = useState<Record<string, any>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadLinks()
  }, [])

  const loadLinks = async () => {
    try {
      console.log('🔗 Loading helpful links...')
      setLoading(true)
      const response = await aiInsightsAPI.getInsights()
      console.log('📥 Links response:', response)
      
      if (response.success && response.links) {
        console.log('✅ Loaded links:', response.links)
        setLinks(response.links)
      } else {
        console.log('ℹ️ No links found')
        setLinks({})
      }
    } catch (error: any) {
      console.error('❌ Error loading links:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-900">
        <Loader2 className="animate-spin text-blue-500" size={48} />
      </div>
    )
  }

  return (
    <div className="w-full h-full flex flex-col bg-gray-900 text-white overflow-y-auto">
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3 bg-gray-800 sticky top-0 z-10">
        <button
          className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white"
          onClick={() => setCurrentPage('ai-insights/engagement')}
        >
          <ArrowLeft />
        </button>
        <div className="text-md font-bold ml-3">Helpful Links</div>
      </div>

      {/* Links List */}
      <div className="p-4">
        {Object.keys(links).length === 0 ? (
          <div className="text-center mt-12">
            <ExternalLink size={48} className="mx-auto text-gray-600 mb-4" />
            <p className="text-gray-400 text-lg">No helpful links available yet</p>
            <p className="text-gray-500 text-sm mt-2">Links will appear here after generating AI insights</p>
          </div>
        ) : (
          Object.entries(links).map(([query, items]: [string, any]) => (
            <div key={query} className="mb-6">
              <h3 className="font-semibold text-lg mb-3 text-blue-400">🔍 {query}</h3>
              {Array.isArray(items) && items.length > 0 ? (
                items.map((item: any, idx: number) => (
                  <a
                    key={idx}
                    href={item.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block p-4 mb-3 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors border border-gray-700 hover:border-blue-500"
                  >
                    <div className="flex justify-between items-start gap-3">
                      <div className="flex-1">
                        <h4 className="font-medium text-blue-300 mb-1">{item.title}</h4>
                        <p className="text-sm text-gray-400 leading-relaxed">{item.snippet}</p>
                        <p className="text-xs text-gray-600 mt-2">{item.link}</p>
                      </div>
                      <ExternalLink size={18} className="text-blue-500 flex-shrink-0 mt-1" />
                    </div>
                  </a>
                ))
              ) : (
                <p className="text-gray-500 text-sm italic">No results found</p>
              )}
            </div>
          ))
        )}
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