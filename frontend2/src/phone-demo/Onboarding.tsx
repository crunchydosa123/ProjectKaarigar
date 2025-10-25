import { useEffect, useState } from "react";
import { Mic, MicOff, House, ClosedCaption } from "lucide-react";
import CircularProgressBar from "@/components/ui/CircularProgressBar";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@radix-ui/react-popover";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { usePage } from "@/contexts/PageContext";

type Message = {
  sender: "user" | "ai";
  text: string;
};

type Props = {
  progress?: number;
};

const Onboarding = ({ progress = 20 }: Props) => {
  const {setCurrentPage} = usePage();
  const [animatedProgress, setAnimatedProgress] = useState(0);
  const [isMuted, setIsMuted] = useState(false);

  // Example conversation
  const messages: Message[] = [
    { sender: "ai", text: "Hi there 👋 Welcome to Conversational Onboarding!" },
    { sender: "ai", text: "I'm your assistant for setting things up easily." },
    { sender: "user", text: "Hey! Sounds good, what do I need to do?" },
    { sender: "ai", text: "We’ll start by connecting your account and adding your first product." },
    { sender: "user", text: "Alright, let’s go!" },
  ];

  useEffect(() => {
    let start = 0;
    const duration = 1500;
    const stepTime = 10;
    const increment = (progress / duration) * stepTime;

    const interval = setInterval(() => {
      start += increment;
      if (start >= progress) {
        start = progress;
        clearInterval(interval);
      }
      setAnimatedProgress(Number(start.toFixed(1)));
    }, stepTime);

    return () => clearInterval(interval);
  }, [progress]);

  const radius = 120;
  const stroke = 6;
  const normalizedRadius = radius - stroke / 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset =
    circumference - (animatedProgress / 100) * circumference;

  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
      style={{ backgroundImage: "url('/white_bg.png')" }}
    >
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3">
        <button className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white" onClick={()=>setCurrentPage('home')}><House /></button>
        <div className="text-md font-bold ml-3">Conversational Onboarding</div>
      </div>

      {/* Progress Section */}
      <div className="w-full flex flex-col justify-start">
        <CircularProgressBar />

        {/* Mic Button */}
        <div className="w-full flex justify-center gap-2">
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
      </div>
    </div>
  );
};

export default Onboarding;
