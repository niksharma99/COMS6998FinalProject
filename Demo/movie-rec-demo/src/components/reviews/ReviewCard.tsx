import { Star, Clock, Trash2, MessageCircle } from 'lucide-react';
import { type TMDBMovie } from '../../types/movie';
import { getPosterUrl } from '../../api/tmdb';

export interface Review {
  movieId: number;
  rating: number;
  text: string;
  createdAt: string;
}

interface ReviewCardProps {
  review: Review;
  movie?: TMDBMovie;
  onDelete?: (movieId: number) => void;
}

function formatDate(date: string) {
  return new Date(date).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export function ReviewCard({ review, movie, onDelete }: ReviewCardProps) {
  return (
    <div className="flex gap-4 bg-gray-800/50 border border-gray-700 rounded-xl p-4 group">
      {/* Poster */}
      {movie?.poster_path ? (
        <img
          src={getPosterUrl(movie.poster_path, 'w200')}
          alt={movie.title}
          className="w-16 h-24 object-cover rounded-lg flex-shrink-0"
        />
      ) : (
        <div className="w-16 h-24 bg-gray-700 rounded-lg flex-shrink-0 flex items-center justify-center">
          <Star className="w-6 h-6 text-gray-600" />
        </div>
      )}

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-white font-semibold leading-tight">
              {movie?.title || 'Movie'}
            </h3>
            {movie && (
              <p className="text-gray-500 text-sm">
                {movie.release_date?.split('-')[0] || 'Year TBA'}
              </p>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            {/* Rating badge */}
            <div className={`flex items-center gap-1.5 rounded-full px-3 py-1 ${
              review.rating >= 8 
                ? 'bg-yellow-500/20 border border-yellow-500/30' 
                : 'bg-gray-700'
            }`}>
              <Star className={`w-4 h-4 ${
                review.rating >= 8 
                  ? 'text-yellow-400 fill-yellow-400' 
                  : 'text-gray-400'
              }`} />
              <span className={`font-semibold text-sm ${
                review.rating >= 8 ? 'text-yellow-400' : 'text-white'
              }`}>
                {review.rating}/10
              </span>
            </div>
            
            {/* Delete button */}
            {onDelete && (
              <button
                onClick={() => onDelete(review.movieId)}
                className="p-1.5 text-gray-600 hover:text-red-500 hover:bg-gray-700 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                title="Delete review"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* High rating indicator */}
        {review.rating >= 8 && (
          <p className="text-xs text-yellow-500/80 mt-1">
            ★ Influencing your recommendations
          </p>
        )}

        {/* Review text */}
        {review.text && (
          <div className="mt-3">
            <div className="flex items-center gap-1.5 text-gray-500 text-xs mb-1">
              <MessageCircle className="w-3 h-3" />
              <span>Your thoughts</span>
            </div>
            <p className="text-gray-300 text-sm whitespace-pre-line line-clamp-3">
              {review.text}
            </p>
          </div>
        )}

        {/* Timestamp */}
        <div className="flex items-center gap-2 text-xs text-gray-500 mt-3">
          <Clock className="w-3.5 h-3.5" />
          <span>Reviewed {formatDate(review.createdAt)}</span>
        </div>
      </div>
    </div>
  );
}