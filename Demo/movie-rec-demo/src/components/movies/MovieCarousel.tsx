import { useEffect, useState, useRef } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { MovieCard } from './MovieCard';
import { Spinner } from '../ui/Spinner';
import { getMovies } from '../../api/tmdb';
import type { TMDBMovie, Recommendation, RecommendedMovie } from '../../types/movie';

interface MovieCarouselProps {
  title: string;
  recommendations: Recommendation[];
  onMovieClick?: (movie: RecommendedMovie) => void;
}

export function MovieCarousel({ title, recommendations, onMovieClick }: MovieCarouselProps) {
  const [movies, setMovies] = useState<RecommendedMovie[]>([]);
  const [loading, setLoading] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const movieIds = recommendations.map(r => r.movieId);
    
    getMovies(movieIds).then((tmdbMovies) => {
      // Combine TMDB data with our recommendation data
      const combined: RecommendedMovie[] = recommendations
        .map(rec => {
          const movie = tmdbMovies.find(m => m.id === rec.movieId);
          if (!movie) return null;
          return {
            movie,
            explanation: rec.explanation,
            matchScore: rec.matchScore,
            factors: rec.factors,
          };
        })
        .filter((m): m is RecommendedMovie => m !== null);
      
      setMovies(combined);
      setLoading(false);
    });
  }, [recommendations]);

  const scroll = (direction: 'left' | 'right') => {
    if (scrollRef.current) {
      const scrollAmount = 400;
      scrollRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth',
      });
    }
  };

  if (loading) {
    return (
      <div className="mb-8">
        <h2 className="text-xl font-bold text-white mb-4">{title}</h2>
        <div className="flex items-center justify-center h-64">
          <Spinner className="w-8 h-8" />
        </div>
      </div>
    );
  }

  return (
    <div className="mb-8 group/carousel">
      <h2 className="text-xl font-bold text-white mb-4">{title}</h2>
      
      <div className="relative">
        {/* Left scroll button */}
        <button
          onClick={() => scroll('left')}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-black/80 hover:bg-black p-2 rounded-full opacity-0 group-hover/carousel:opacity-100 transition-opacity"
        >
          <ChevronLeft className="w-6 h-6 text-white" />
        </button>

        {/* Scrollable container */}
        <div
          ref={scrollRef}
          className="flex gap-4 overflow-x-auto scrollbar-hide pb-4"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {movies.map((rec) => (
            <MovieCard
              key={rec.movie.id}
              movie={rec.movie}
              explanation={rec.explanation}
              matchScore={rec.matchScore}
              onClick={() => onMovieClick?.(rec)}
            />
          ))}
        </div>

        {/* Right scroll button */}
        <button
          onClick={() => scroll('right')}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-10 bg-black/80 hover:bg-black p-2 rounded-full opacity-0 group-hover/carousel:opacity-100 transition-opacity"
        >
          <ChevronRight className="w-6 h-6 text-white" />
        </button>
      </div>
    </div>
  );
}