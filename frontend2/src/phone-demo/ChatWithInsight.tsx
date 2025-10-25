import { usePage } from '@/contexts/PageContext'
import { House, Send } from 'lucide-react'
import React, { useState, useRef, useEffect } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

type Props = {
  startMessage: string
}

type Message = {
  id: number
  text: string
  sender: 'ai' | 'user'
}

const ChatWithInsight = ({ startMessage }: Props) => {
  const { setCurrentPage } = usePage()
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, text: startMessage, sender: 'ai' }
  ])
  const [input, setInput] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)

  const handleSend = () => {
    if (!input.trim()) return
    const newMessage: Message = {
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

export default ChatWithInsight
