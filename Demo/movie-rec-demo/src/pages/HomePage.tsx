import { useState, useEffect } from 'react';
import { MovieCarousel } from '../components/movies/MovieCarousel';
import { MovieModal } from '../components/movies/MovieModal';
import { ChatToggle } from '../components/chat/ChatToggle';
import { ChatWindow } from '../components/chat/ChatWindow';
import { OnboardingModal } from '../components/onboarding/OnboardingModal';
import { mockRecommendationSets } from '../data/mockRecommendations';
import { getStoredRecommendations, generatePersonalizedRecommendations } from '../api/recommendations';
import type { RecommendedMovie, Recommendation } from '../types/movie';
import type { OnboardingData } from '../types/user';
import { Spinner } from '../components/ui/Spinner';

interface RecommendationSet {
  title: string;
  recommendations: Recommendation[];
}

export function HomePage() {
  const [selectedMovie, setSelectedMovie] = useState<RecommendedMovie | null>(null);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatMovieContext, setChatMovieContext] = useState<RecommendedMovie | null>(null);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [recommendationSets, setRecommendationSets] = useState<Record<string, RecommendationSet> | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load recommendations
  useEffect(() => {
    async function loadRecommendations() {
      // Check for personalized recommendations first
      const personalized = getStoredRecommendations();
      
      if (personalized && personalized.length > 0) {
        // Convert to the format our carousels expect
        const sets: Record<string, RecommendationSet> = {};
        personalized.forEach((set, index) => {
          sets[`personalized-${index}`] = {
            title: set.title,
            recommendations: set.recommendations,
          };
        });
        setRecommendationSets(sets);
      } else {
        // Fall back to mock data
        setRecommendationSets(mockRecommendationSets);
      }
      
      setIsLoading(false);
    }

    loadRecommendations();
  }, []);

  // Check if user needs onboarding
  useEffect(() => {
    const onboardingData = localStorage.getItem('onboardingData');
    const tmdbMovieData = localStorage.getItem('tmdbMovieData');
    const personalizedRecs = localStorage.getItem('personalizedRecommendations');
    
    // Show onboarding if:
    // - They haven't completed onboarding yet
    // - AND they don't have TMDB movie data
    // - AND they don't have personalized recommendations yet
    if (!onboardingData && !personalizedRecs) {
      const tmdbData = tmdbMovieData ? JSON.parse(tmdbMovieData) : null;
      const hasTMDBData = tmdbData && (
        tmdbData.ratedMovies?.length > 3 || 
        tmdbData.favoriteMovies?.length > 3
      );
      
      if (!hasTMDBData) {
        setShowOnboarding(true);
      }
    }
  }, []);

  const handleTalkToChat = () => {
    setChatMovieContext(selectedMovie);
    setIsChatOpen(true);
    setSelectedMovie(null);
  };

  const handleChatClose = () => {
    setIsChatOpen(false);
    setChatMovieContext(null);
  };

  const handleChatToggle = () => {
    if (isChatOpen) {
      handleChatClose();
    } else {
      setChatMovieContext(null);
      setIsChatOpen(true);
    }
  };

  const handleOnboardingComplete = async (data: OnboardingData) => {
    console.log('Onboarding complete:', data);
    localStorage.setItem('onboardingData', JSON.stringify(data));
    setShowOnboarding(false);
    
    // Generate personalized recommendations
    setIsLoading(true);
    try {
      await generatePersonalizedRecommendations();
      const personalized = getStoredRecommendations();
      if (personalized && personalized.length > 0) {
        const sets: Record<string, RecommendationSet> = {};
        personalized.forEach((set, index) => {
          sets[`personalized-${index}`] = {
            title: set.title,
            recommendations: set.recommendations,
          };
        });
        setRecommendationSets(sets);
      }
    } catch (error) {
      console.error('Failed to generate recommendations:', error);
    }
    setIsLoading(false);
  };

  const handleOnboardingSkip = () => {
    localStorage.setItem('onboardingData', JSON.stringify({ skipped: true }));
    setShowOnboarding(false);
  };

  // Get user name for greeting
  const user = localStorage.getItem('user');
  const userName = user ? JSON.parse(user).name : null;

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Hero section */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          {userName ? `Welcome back, ${userName}!` : 'Welcome Back!'}
        </h1>
        <p className="text-gray-400">
          Here are your personalized movie recommendations
        </p>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <Spinner className="w-10 h-10" />
        </div>
      )}

      {/* Recommendation carousels */}
      {!isLoading && recommendationSets && Object.entries(recommendationSets).map(([key, { title, recommendations }]) => (
        <MovieCarousel
          key={key}
          title={title}
          recommendations={recommendations}
          onMovieClick={setSelectedMovie}
        />
      ))}

      {/* Movie detail modal */}
      {selectedMovie && (
        <MovieModal
          movie={selectedMovie}
          onClose={() => setSelectedMovie(null)}
          onTalkToChat={handleTalkToChat}
        />
      )}

      {/* Chat components */}
      <ChatToggle
        isOpen={isChatOpen}
        onClick={handleChatToggle}
      />
      {isChatOpen && (
        <ChatWindow
          onClose={handleChatClose}
          movieContext={chatMovieContext}
        />
      )}

      {/* Onboarding modal for new users */}
      {showOnboarding && (
        <OnboardingModal
          onComplete={handleOnboardingComplete}
          onSkip={handleOnboardingSkip}
        />
      )}
    </div>
  );
}