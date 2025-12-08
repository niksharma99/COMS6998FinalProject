import { Star } from 'lucide-react';
import { type TMDBMovie, GENRE_MAP } from '../../types/movie';
import { getPosterUrl } from '../../api/tmdb';

interface MovieCardProps {
  movie: TMDBMovie;
  explanation?: string;
  matchScore?: number;
  onClick?: () => void;
}

export function MovieCard({ movie, explanation, matchScore, onClick }: MovieCardProps) {
  const year = movie.release_date?.split('-')[0] || 'TBA';
  const genre = movie.genre_ids?.[0] ? GENRE_MAP[movie.genre_ids[0]] : '';

  return (
    <div
      onClick={onClick}
      className="group cursor-pointer flex-shrink-0 w-44"
    >
      {/* Poster */}
      <div className="relative aspect-[2/3] rounded-lg overflow-hidden mb-3">
        <img
          src={getPosterUrl(movie.poster_path, 'w300')}
          alt={movie.title}
          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
        />
        
        {/* Hover overlay with explanation */}
        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/70 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 p-4 flex flex-col justify-end">
          {matchScore && (
            <div className="mb-2">
              <span className="bg-red-600 text-white text-xs font-bold px-2 py-1 rounded">
                {matchScore}% Match
              </span>
            </div>
          )}
          
          {explanation && (
            <p className="text-white text-xs line-clamp-3">
              {explanation}
            </p>
          )}
          
          <div className="flex items-center gap-2 mt-2">
            <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
            <span className="text-white text-sm">{movie.vote_average.toFixed(1)}</span>
          </div>
        </div>
      </div>

      {/* Title and meta */}
      <h3 className="text-white text-sm font-medium mb-1 group-hover:text-red-500 transition-colors line-clamp-1">
        {movie.title}
      </h3>
      
      <div className="flex items-center gap-2 text-xs text-gray-400">
        <span>{year}</span>
        {genre && (
          <>
            <span>•</span>
            <span>{genre}</span>
          </>
        )}
      </div>
    </div>
  );
}