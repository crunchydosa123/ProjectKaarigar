import { usePage } from "@/contexts/PageContext"
import { ClosedCaption, Download, House, Mic, MicOff, Save } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@radix-ui/react-popover";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useState } from "react";
import { Button } from "@/components/ui/button";

type Message = {
  sender: "user" | "ai";
  text: string;
};


const CreateLogo = () => {
  const { setCurrentPage } = usePage();
  const [isMuted, setIsMuted] = useState(false);
  const messages: Message[] = [
    { sender: "ai", text: "Hi there 👋 Welcome to Conversational Onboarding!" },
    { sender: "ai", text: "I'm your assistant for setting things up easily." },
    { sender: "user", text: "Hey! Sounds good, what do I need to do?" },
    { sender: "ai", text: "We’ll start by connecting your account and adding your first product." },
    { sender: "user", text: "Alright, let’s go!" },
  ]

  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
      style={{ backgroundImage: "url('/white_bg.png')" }}
    >
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3">
        <button className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white" onClick={() => setCurrentPage('home')}><House /></button>
        <div className="text-md font-bold ml-3">Create Logo with AI</div>
      </div>

      <div className="relative w-full h-[300px] bg-gray-800 border overflow-hidden rounded-lg">
        {/* Top bar with buttons */}
        <div className="absolute top-10 right-3 flex gap-2 z-10">
          <button className="bg-yellow-500 hover:bg-blue-600 text-white flex justify-center items-center w-10 h-10 text-xs px-3 py-1 rounded-sm shadow">
            <Download />
          </button>
          <button className="bg-green-500 hover:bg-green-600 flex justify-center items-center w-10 h-10 text-white text-xs px-3 py-1 rounded-md shadow">
            <Save />
          </button>
        </div>

        {/* X-axis scale */}
        <div className="absolute top-0 left-10 right-0 h-8 flex items-end border-b text-[10px] text-white">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="w-10 text-center border-l border-gray-200">
              {i * 20}
            </div>
          ))}
        </div>

        {/* Y-axis scale */}
        <div className="absolute top-8 bottom-0 left-0 w-10 flex flex-col items-end border-r text-[10px] text-white">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="h-10 border-t border-gray-200 pr-1">
              {i * 20}
            </div>
          ))}
        </div>

        {/* Main canvas area */}
        <div className="absolute top-8 left-10 right-0 bottom-0 bg-gray-400">
          {/* Square placeholder in center */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-40 h-40 border-2 border-dashed border-gray-600 rounded-lg flex items-center justify-center text-white text-sm">
              <img src={'/ai_gen_logo.jpeg'} />
            </div>
          </div>
        </div>
      </div>

      <Card className="mx-2 py-4 bg-yellow-100 mt-4">
        <CardContent>
      <div className="flex justify-start  text-sm font-bold">Edit and Generate logos using your voice over Conversational AI</div>    
      <div className="mt-2 px-5 flex justify-center items-center gap-2">
        <button
          onClick={() => setIsMuted(!isMuted)}
          className={`flex items-center gap-2 p-5 rounded-md transition text-white
              ${isMuted ? "bg-green-500 hover:bg-green-400" : "bg-red-500 hover:bg-red-400"}`}
        >
          {isMuted ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
        </button>
        <Popover>
          <PopoverTrigger>
            <Button variant="outline" className="w-15 h-15">
              <ClosedCaption className="w-10 h-10" />
            </Button>
          </PopoverTrigger>

          <PopoverContent
            align="center"
            side="top"
            className="fixed left-1/2 top-1/2 -translate-x-3/4 -translate-y-1/2 w-60 h-80 border-none bg-transparent shadow-none"
          >
            <Card className="w-full h-full flex flex-col">
              <CardHeader>
                <CardTitle>Conversation Transcript</CardTitle>
              </CardHeader>

              <CardContent className="text-sm flex-1 overflow-y-auto space-y-3 p-2">
                {messages.map((msg, index) => (
                  <div
                    key={index}
                    className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"
                      }`}
                  >
                    <div
                      className={`px-3 py-2 rounded-2xl max-w-[75%] ${msg.sender === "user"
                        ? "bg-blue-600 text-white rounded-br-none"
                        : "bg-gray-200 text-gray-900 rounded-bl-none"
                        }`}
                    >
                      {msg.text}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </PopoverContent>
        </Popover>
      </div>
        </CardContent>
      </Card>    

    </div>
  )
}

export default CreateLogo