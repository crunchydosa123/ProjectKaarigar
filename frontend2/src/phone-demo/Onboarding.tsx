import { useEffect, useState, useRef } from "react";
import { Mic, MicOff, House, ClosedCaption, Send, Volume2, VolumeX } from "lucide-react";
import CircularProgressBar from "@/components/ui/CircularProgressBar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@radix-ui/react-popover";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { usePage } from "@/contexts/PageContext";

type Message = {
  sender: "user" | "ai";
  text: string;
  timestamp?: string;
  inputType?: "text" | "audio";
};

type Props = {
  progress?: number;
};

const Onboarding = ({}: Props) => {
  const { setCurrentPage } = usePage();
  const [animatedProgress, setAnimatedProgress] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentMessage, setCurrentMessage] = useState("");
  const [kaarigarId, setKaarigarId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [userResponseCount, setUserResponseCount] = useState(0);
  const [error, setError] = useState("");
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [recordingStartTime, setRecordingStartTime] = useState<number | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  // API functions
  const startConversation = async () => {
    try {
      setIsLoading(true);
      setError("");
      
      /*const response = await fetch('https://backend-557742533869.asia-south1.run.app/api/conversational/start', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });*/

      const response = await fetch('/api/conversational/start', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        console.log(response);
        throw new Error('Failed to start conversation');
      }

      const data = await response.json();
      setKaarigarId(data.kaarigar_id);
      
      // Start with empty messages - no initial greeting
      console.log('🎤 CONVERSATION STARTED - Setting empty messages array');
      setMessages([]);
      setUserResponseCount(0);
      setIsComplete(false);
      
      // Play initial AI audio if available
      if (data.ai_audio) {
        playAudio(data.ai_audio);
      }
    } catch (error) {
      console.error('Error starting conversation:', error);
      setError('Failed to start conversation. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const playAudio = (audioBase64: string) => {
    if (!audioEnabled) return;
    
    try {
      const audioBlob = new Blob([Uint8Array.from(atob(audioBase64), c => c.charCodeAt(0))], { type: 'audio/mpeg' });
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      
      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
      };
      
      audio.play().catch(error => {
        console.error('Error playing audio:', error);
        URL.revokeObjectURL(audioUrl);
      });
    } catch (error) {
      console.error('Error creating audio from base64:', error);
    }
  };

  const sendTextMessage = async (message: string) => {
    if (!kaarigarId || !message.trim()) return;

    try {
      setIsLoading(true);
      setError("");

      // Clear the input field immediately
      setCurrentMessage("");

      /*const response = await fetch('https://backend-557742533869.asia-south1.run.app/api/conversational/message', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          kaarigar_id: kaarigarId,
          message: message
        }),
      });*/

      const response = await fetch('/api/conversational/message', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          kaarigar_id: kaarigarId,
          message: message
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data = await response.json();
      
      // Fetch the updated conversation status to get the full conversation history
      try {
        /*const statusResponse = await fetch(`https://backend-557742533869.asia-south1.run.app/api/conversational/status/${kaarigarId}`, {
          credentials: 'include'
        });*/

        const statusResponse = await fetch(`/api/conversational/status/${kaarigarId}`, {
          credentials: 'include'
        });
        
        if (statusResponse.ok) {
          const statusData = await statusResponse.json();
          console.log('📋 Full conversation history:', statusData.conversation_history);
          
          if (statusData.conversation_history && statusData.conversation_history.length > 0) {
            // Convert backend conversation history to frontend message format
            const conversationMessages: Message[] = statusData.conversation_history.map((msg: any) => ({
              sender: msg.role === "user" ? "user" : "ai",
              text: msg.text,
              timestamp: msg.timestamp,
              inputType: msg.input_type || "text"
            }));
            
            // Replace all messages with the complete conversation history
            console.log('🔄 REPLACING MESSAGES WITH CONVERSATION HISTORY:', conversationMessages.length, 'messages');
            conversationMessages.forEach((msg, index) => {
              console.log(`   Message ${index + 1}: ${msg.sender} - ${msg.text.substring(0, 50)}...`);
            });
            setMessages(conversationMessages);
            console.log('✅ Messages updated in frontend:', conversationMessages.length, 'messages');
          } else {
            console.log('⚠️ No conversation history found');
            // Fallback: just add the AI response to existing messages
            const responseAiMsg: Message = {
              sender: "ai",
              text: data.ai_message,
              timestamp: new Date().toISOString()
            };
            setMessages(prev => [...prev, responseAiMsg]);
          }
        } else {
          console.error('❌ Failed to fetch conversation status:', statusResponse.status);
          // Fallback: just add the AI response
          const responseAiMsg: Message = {
            sender: "ai",
            text: data.ai_message,
            timestamp: new Date().toISOString()
          };
          setMessages(prev => [...prev, responseAiMsg]);
        }
      } catch (error) {
        console.error('❌ Error fetching conversation status:', error);
        // Fallback: just add the AI response
        const responseAiMsg: Message = {
          sender: "ai",
          text: data.ai_message,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, responseAiMsg]);
      }
      
      // Play AI audio response if available
      if (data.ai_audio) {
        playAudio(data.ai_audio);
      }
      
      setUserResponseCount(data.user_response_count);
      setIsComplete(data.is_complete);

      if (data.is_complete && data.profile) {
        console.log('Profile generated:', data.profile);
        // You can handle profile completion here
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setError('Failed to send message. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const sendAudioMessage = async (audioBlob: Blob) => {
    if (!kaarigarId) return;

    try {
      setIsLoading(true);
      setError("");

      // Convert audio to base64
      const reader = new FileReader();
      reader.onload = async () => {
        const base64Audio = (reader.result as string).split(',')[1];
        
        /*const response = await fetch('https://backend-557742533869.asia-south1.run.app/api/conversational/audio-message', {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            kaarigar_id: kaarigarId,
            audio: base64Audio,
            language_code: 'en'
          }),
        });*/

        const response = await fetch('/api/conversational/audio-message', {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            kaarigar_id: kaarigarId,
            audio: base64Audio,
            language_code: 'en'
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to send audio message');
        }

        const data = await response.json();
        
        // Check if transcription was successful
        if (data.transcribed_text && data.transcribed_text.trim()) {
          // Fetch the updated conversation status to get the full conversation history
          try {
            /*const statusResponse = await fetch(`https://backend-557742533869.asia-south1.run.app/api/conversational/status/${kaarigarId}`, {
              credentials: 'include'
            });*/

            const statusResponse = await fetch(`/api/conversational/status/${kaarigarId}`, {
              credentials: 'include'
            });
            
            if (statusResponse.ok) {
              const statusData = await statusResponse.json();
              console.log('📋 Full conversation history (audio):', statusData.conversation_history);
              
              if (statusData.conversation_history && statusData.conversation_history.length > 0) {
                // Convert backend conversation history to frontend message format
                const conversationMessages: Message[] = statusData.conversation_history.map((msg: any) => ({
                  sender: msg.role === "user" ? "user" : "ai",
                  text: msg.text,
                  timestamp: msg.timestamp,
                  inputType: msg.input_type || "text"
                }));
                
            // Replace all messages with the complete conversation history
            console.log('🔄 REPLACING MESSAGES WITH CONVERSATION HISTORY (AUDIO):', conversationMessages.length, 'messages');
            conversationMessages.forEach((msg, index) => {
              console.log(`   Message ${index + 1}: ${msg.sender} - ${msg.text.substring(0, 50)}...`);
            });
            setMessages(conversationMessages);
            console.log('✅ Messages updated in frontend (audio):', conversationMessages.length, 'messages');
              } else {
                console.log('⚠️ No conversation history found (audio)');
                // Fallback: just add the messages manually
                const userMsg: Message = {
                  sender: "user",
                  text: data.transcribed_text,
                  timestamp: new Date().toISOString(),
                  inputType: "audio"
                };
                const aiMessage: Message = {
                  sender: "ai",
                  text: data.ai_message,
                  timestamp: new Date().toISOString()
                };
                setMessages(prev => [...prev, userMsg, aiMessage]);
              }
            } else {
              console.error('❌ Failed to fetch conversation status (audio):', statusResponse.status);
            }
          } catch (error) {
            console.error('❌ Error fetching conversation status (audio):', error);
            // Fallback: just add the messages manually
            const userMsg: Message = {
              sender: "user",
              text: data.transcribed_text,
              timestamp: new Date().toISOString(),
              inputType: "audio"
            };
            const aiMessage: Message = {
              sender: "ai",
              text: data.ai_message,
              timestamp: new Date().toISOString()
            };
            setMessages(prev => [...prev, userMsg, aiMessage]);
          }
          
          // Play AI audio response if available
          if (data.ai_audio) {
            playAudio(data.ai_audio);
          }
          
          setUserResponseCount(data.user_response_count);
          setIsComplete(data.is_complete);

          if (data.is_complete && data.profile) {
            console.log('Profile generated:', data.profile);
          }
        } else {
          // Transcription failed or no speech detected
          setError('Could not understand your voice. Please try speaking more clearly or use text input.');
        }
      };
      
      reader.readAsDataURL(audioBlob);
    } catch (error) {
      console.error('Error sending audio message:', error);
      setError('Failed to send audio message. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Audio recording functions
  const startRecording = async () => {
    try {
      // Request microphone with better audio constraints
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 44100,
          channelCount: 1
        } 
      });
      streamRef.current = stream;
      
      // Create MediaRecorder with better settings
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus' // Better compression and quality
      });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        
        // Check if we have meaningful audio (not just silence/noise)
        if (audioBlob.size > 5000) { // At least 5KB of audio data for better quality
          sendAudioMessage(audioBlob);
        } else {
          setError('No audio detected. Please speak clearly into the microphone for at least 2 seconds.');
        }
        
        // Clean up
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
      };

      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event);
        setError('Recording error occurred. Please try again.');
        setIsRecording(false);
      };

      mediaRecorder.start(100); // Collect data every 100ms
      setIsRecording(true);
      setRecordingStartTime(Date.now());
      setError(""); // Clear any previous errors
      
    } catch (error) {
      console.error('Error starting recording:', error);
      if (error instanceof Error) {
        if (error.name === 'NotAllowedError') {
          setError('Microphone access denied. Please allow microphone permissions and refresh the page.');
        } else if (error.name === 'NotFoundError') {
          setError('No microphone found. Please connect a microphone and try again.');
        } else {
          setError('Failed to access microphone. Please check your device settings.');
        }
      } else {
        setError('Failed to access microphone. Please check your device settings.');
      }
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      const recordingDuration = recordingStartTime ? Date.now() - recordingStartTime : 0;
      
      // Check minimum recording duration (at least 2 seconds for better quality)
      if (recordingDuration < 2000) {
        setError('Please record for at least 2 seconds. Try speaking a bit longer.');
        setIsRecording(false);
        setRecordingStartTime(null);
        return;
      }
      
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setRecordingStartTime(null);
    }
  };

  const handleMicClick = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const handleSendMessage = () => {
    if (currentMessage.trim()) {
      sendTextMessage(currentMessage);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Check microphone permissions on component mount
  useEffect(() => {
    const checkMicrophonePermission = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => track.stop());
        console.log('✅ Microphone permission granted');
      } catch (error) {
        console.error('❌ Microphone permission denied:', error);
        setError('Microphone access is required for voice conversations. Please allow microphone permissions and refresh the page.');
      }
    };

    checkMicrophonePermission();
  }, []);

  // Load existing conversation or start new one
  useEffect(() => {
    if (!kaarigarId) {
      startConversation();
    } else {
      // Load existing conversation history
      loadConversationHistory();
    }
  }, [kaarigarId]);

  // Function to load existing conversation history
  const loadConversationHistory = async () => {
    if (!kaarigarId) return;
    
    try {
      /*const statusResponse = await fetch(`https://backend-557742533869.asia-south1.run.app/api/conversational/status/${kaarigarId}`, {
        credentials: 'include'
      });*/
      
      const statusResponse = await fetch(`/api/conversational/status/${kaarigarId}`, {
        credentials: 'include'
      });

      if (statusResponse.ok) {
        const statusData = await statusResponse.json();
        console.log('📋 Loading existing conversation history:', statusData.conversation_history);
        
        if (statusData.conversation_history && statusData.conversation_history.length > 0) {
          // Convert backend conversation history to frontend message format
          const conversationMessages: Message[] = statusData.conversation_history.map((msg: any) => ({
            sender: msg.role === "user" ? "user" : "ai",
            text: msg.text,
            timestamp: msg.timestamp,
            inputType: msg.input_type || "text"
          }));
          setMessages(conversationMessages);
          
          // Update progress
          const userResponses = conversationMessages.filter(msg => msg.sender === "user");
          setUserResponseCount(userResponses.length);
          setIsComplete(userResponses.length >= 6);
          
          console.log('✅ Loaded existing conversation:', conversationMessages.length, 'messages');
        }
      }
    } catch (error) {
      console.error('❌ Error loading conversation history:', error);
    }
  };

  // Update progress based on user responses
  useEffect(() => {
    const progressPercentage = (userResponseCount / 6) * 100;
    setAnimatedProgress(progressPercentage);
  }, [userResponseCount]);

  // Remove unused variables

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
        <CircularProgressBar progress={animatedProgress} />
        
        {/* Progress Text */}
        <div className="text-center mt-2">
          <p className="text-sm text-gray-600">
            {userResponseCount}/6 responses completed
          </p>
          {isComplete && (
            <>
            <p className="text-sm text-green-600 font-medium">
              ✅ Profile generated successfully!
            </p>
            <button className="p-1 bg-blue-600 w-1/3 rounded-md text-white my-1" onClick={()=> setCurrentPage('onboarding/details')}>Next</button>
            </>
          )}<button className="p-1 bg-blue-600 w-1/3 rounded-md text-white my-1" onClick={()=> setCurrentPage('onboarding/details')}>Next</button>'
        </div>

        {/* Error Display */}
        {error && (
          <div className="text-center mt-2">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* Recording Status */}
        {isRecording && (
          <div className="text-center mt-2">
            <div className="flex items-center justify-center gap-2">
              <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
              <p className="text-sm text-red-600 font-medium">Recording... Speak clearly</p>
            </div>
            <p className="text-xs text-gray-500 mt-1">Hold the mic button and speak for at least 2 seconds</p>
          </div>
        )}

        {/* Instructions */}
        {!isRecording && !isLoading && (
          <div className="text-center mt-2">
            <p className="text-xs text-gray-600">
              💡 <strong>Tip:</strong> Hold the mic button and speak clearly, or type your response below
            </p>
          </div>
        )}

        {/* Conversation Controls */}
        <div className="w-full flex justify-center gap-2 mt-4">
          <button
            onClick={handleMicClick}
            disabled={isLoading || isComplete}
            className={`flex items-center gap-2 p-5 rounded-md transition text-white disabled:opacity-50
              ${isRecording ? "bg-green-500 hover:bg-red-400 animate-pulse" : "bg-red-500 hover:bg-green-400"}`}
          >
            {isRecording ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
          </button>

          <button
            onClick={() => setAudioEnabled(!audioEnabled)}
            className={`flex items-center gap-2 p-5 rounded-md transition text-white
              ${audioEnabled ? "bg-blue-500 hover:bg-blue-400" : "bg-gray-500 hover:bg-gray-400"}`}
          >
            {audioEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
          </button>

          {/*<Popover>
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
                  {messages.length === 0 ? (
                    <p className="text-gray-500 text-center">No messages yet...</p>
                  ) : (
                    messages.map((msg, index) => (
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
                          <div className="text-xs opacity-70 mb-1">
                            {msg.inputType === "audio" && "🎤 "}
                            {msg.sender === "ai" && "🔊 "}
                            {msg.sender === "user" ? "You" : "AI"}
                          </div>
                        {msg.text}
                      </div>
                    </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </PopoverContent>
          </Popover>*/}
        </div>

        {/* Text Input */}
        <div className="w-full px-4 mt-4">
          <div className="flex gap-2">
            <Input
              value={currentMessage}
              onChange={(e) => setCurrentMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your response..."
              disabled={isLoading || isComplete}
              className="flex-1"
            />
            <Button
              onClick={handleSendMessage}
              disabled={!currentMessage.trim() || isLoading || isComplete}
              size="sm"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Loading Indicator */}
        {isLoading && (
          <div className="text-center mt-2">
            <p className="text-sm text-blue-600">Processing...</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Onboarding;
