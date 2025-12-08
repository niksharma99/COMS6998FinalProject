import { useState } from 'react';
import { MovieCarousel } from '../components/movies/MovieCarousel';
import { MovieModal } from '../components/movies/MovieModal';
import { ChatToggle } from '../components/chat/ChatToggle';
import { ChatWindow } from '../components/chat/ChatWindow';
import { mockRecommendationSets } from '../data/mockRecommendations';
import { type RecommendedMovie } from '../types/movie';

export function HomePage() {
  const [selectedMovie, setSelectedMovie] = useState<RecommendedMovie | null>(null);
  const [isChatOpen, setIsChatOpen] = useState(false);

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Hero section */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          Welcome Back!
        </h1>
        <p className="text-gray-400">
          Here are your personalized movie recommendations
        </p>
      </div>

      {/* Recommendation carousels */}
      {Object.entries(mockRecommendationSets).map(([key, { title, recommendations }]) => (
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
        />
      )}

      {/* Chat components */}
      <ChatToggle 
        isOpen={isChatOpen} 
        onClick={() => setIsChatOpen(!isChatOpen)} 
      />
      {isChatOpen && (
        <ChatWindow onClose={() => setIsChatOpen(false)} />
      )}
    </div>
  );
}