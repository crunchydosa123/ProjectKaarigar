import React, { useState, useEffect } from 'react'
import { usePage } from '@/contexts/PageContext'
import { ArrowLeft, ArrowRight, Send } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { motion, AnimatePresence } from 'framer-motion'

type Props = {}

const AIInsights2 = (props: Props) => {
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

export default AIInsights2
