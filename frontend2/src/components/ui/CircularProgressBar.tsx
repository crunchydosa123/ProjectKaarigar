import React, { useEffect, useState } from 'react'

type Message = {
  sender: "user" | "ai";
  text: string;
};

type Props = {
  progress?: number;
};

const CircularProgressBar = ({ progress = 20 }: Props) => {
  const [animatedProgress, setAnimatedProgress] = useState(0);
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
      <div className="flex justify-center items-start">
        <div className="relative h-80 w-80 flex justify-center items-center">
          <svg
            height={radius * 2}
            width={radius * 2}
            className="absolute"
            style={{ transform: "rotate(-90deg)" }}
          >
            <circle
              stroke="#8ABDFF"
              fill="transparent"
              strokeWidth={stroke}
              r={normalizedRadius}
              cx={radius}
              cy={radius}
            />
            <circle
              stroke="#3b82f6"
              fill="transparent"
              strokeWidth={stroke}
              strokeLinecap="round"
              strokeDasharray={`${circumference} ${circumference}`}
              strokeDashoffset={strokeDashoffset}
              r={normalizedRadius}
              cx={radius}
              cy={radius}
              style={{
                transition: "stroke-dashoffset 0.2s ease-out",
              }}
            />
          </svg>

          <div
            className="h-80 w-80 flex justify-center bg-cover bg-center"
            style={{ backgroundImage: "url('/onboarding_agent_icon.png')" }}
          ></div>

          <div className="absolute text-xs font-semibold text-gray-800">
            {Math.round(animatedProgress)}% Complete
          </div>
        </div>
      </div>
  )
}

export default CircularProgressBar