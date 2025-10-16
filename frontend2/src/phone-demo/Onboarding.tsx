import { useEffect, useState } from "react";
import { Mic, MicOff, House } from "lucide-react";
import CircularProgressBar from "@/components/ui/CircularProgressBar";

type Message = {
  sender: "user" | "ai";
  text: string;
};

type Props = {
  progress?: number;
};

const Onboarding = ({ progress = 20 }: Props) => {
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
        <div className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white"><House /></div>
        <div className="text-md font-bold ml-3">Conversational Onboarding</div>
      </div>

      {/* Progress Section */}
      <div className="w-full flex flex-col justify-start">
      <CircularProgressBar />

      {/* Mic Button */}
      <div className="w-full flex justify-center">
        <button
          onClick={() => setIsMuted(!isMuted)}
          className={`flex items-center gap-2 p-5 rounded-md transition text-white
              ${isMuted ? "bg-green-500 hover:bg-green-400" : "bg-red-500 hover:bg-red-400"}`}
        >
          {isMuted ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
        </button>
      </div>

      {/* Conversation Section */}
      <div className="flex flex-col flex-grow px-4 py-4 overflow-y-auto space-y-3">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`px-4 py-2 rounded-2xl max-w-[70%] text-sm ${
                msg.sender === "user"
                  ? "bg-blue-500 text-white rounded-br-none"
                  : "bg-gray-200 text-gray-800 rounded-bl-none"
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}
      </div>
      </div>
    </div>
  );
};

export default Onboarding;
