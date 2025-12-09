import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Film, Sparkles, Brain, Clapperboard, Heart } from 'lucide-react';

const LOADING_MESSAGES = [
  { icon: Brain, text: "Analyzing your movie taste..." },
  { icon: Heart, text: "Finding films you'll love..." },
  { icon: Clapperboard, text: "Curating your recommendations..." },
  { icon: Sparkles, text: "Adding the finishing touches..." },
];

interface PersonalizingPageProps {
  onComplete?: () => void;
}

export function PersonalizingPage() {
  const [messageIndex, setMessageIndex] = useState(0);
  const [progress, setProgress] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    // Cycle through messages
    const messageInterval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % LOADING_MESSAGES.length);
    }, 1500);

    // Update progress bar
    const progressInterval = setInterval(() => {
      setProgress((prev) => Math.min(prev + 2, 100));
    }, 100);

    // Complete after ~5 seconds (or when real processing is done)
    const completeTimeout = setTimeout(async () => {
      // Generate recommendations before navigating
      try {
        const { generatePersonalizedRecommendations } = await import('../api/recommendations');
        await generatePersonalizedRecommendations();
      } catch (error) {
        console.error('Failed to generate recommendations:', error);
      }
      navigate('/');
    }, 5000);

    return () => {
      clearInterval(messageInterval);
      clearInterval(progressInterval);
      clearTimeout(completeTimeout);
    };
  }, [navigate]);

  const CurrentIcon = LOADING_MESSAGES[messageIndex].icon;

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="text-center max-w-md px-4">
        {/* Logo */}
        <div className="flex items-center justify-center gap-2 mb-8">
          <Film className="w-10 h-10 text-red-600" />
          <span className="text-2xl font-bold text-white">ReelReason</span>
        </div>

        {/* Animated icon */}
        <div className="relative w-24 h-24 mx-auto mb-8">
          <div className="absolute inset-0 bg-red-600/20 rounded-full animate-ping" />
          <div className="relative w-full h-full bg-gray-900 rounded-full flex items-center justify-center border-2 border-red-600">
            <CurrentIcon className="w-10 h-10 text-red-500 animate-pulse" />
          </div>
        </div>

        {/* Message */}
        <p className="text-xl text-white mb-2 transition-all duration-300">
          {LOADING_MESSAGES[messageIndex].text}
        </p>
        <p className="text-gray-400 text-sm mb-8">
          This will only take a moment
        </p>

        {/* Progress bar */}
        <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-red-600 to-red-400 transition-all duration-200"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-gray-500 text-xs mt-2">{progress}%</p>
      </div>
    </div>
  );
}