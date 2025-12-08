import { X, Star, Clock, Calendar } from 'lucide-react';
import { type RecommendedMovie, GENRE_MAP } from '../../types/movie';
import { getPosterUrl, getBackdropUrl } from '../../api/tmdb';

interface MovieModalProps {
  movie: RecommendedMovie;
  onClose: () => void;
}

export function MovieModal({ movie, onClose }: MovieModalProps) {
  const { movie: m, explanation, matchScore, factors } = movie;
  const year = m.release_date?.split('-')[0] || 'TBA';
  const genres = m.genre_ids?.map(id => GENRE_MAP[id]).filter(Boolean) || [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/80 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative bg-gray-900 rounded-xl max-w-3xl w-full max-h-[90vh] overflow-hidden">
        {/* Backdrop image */}
        {m.backdrop_path && (
          <div className="absolute inset-0 opacity-20">
            <img
              src={getBackdropUrl(m.backdrop_path)}
              alt=""
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/80 to-gray-900/40" />
          </div>
        )}

        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 p-2 bg-black/50 hover:bg-black/80 rounded-full transition-colors"
        >
          <X className="w-5 h-5 text-white" />
        </button>

        {/* Content */}
        <div className="relative p-6 flex gap-6 overflow-y-auto max-h-[90vh]">
          {/* Poster */}
          <div className="flex-shrink-0">
            <img
              src={getPosterUrl(m.poster_path, 'w300')}
              alt={m.title}
              className="w-48 rounded-lg shadow-xl"
            />
          </div>

          {/* Details */}
          <div className="flex-1 min-w-0">
            <h2 className="text-3xl font-bold text-white mb-2">{m.title}</h2>
            
            {/* Meta info */}
            <div className="flex flex-wrap items-center gap-4 text-gray-400 mb-4">
              <div className="flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                <span>{year}</span>
              </div>
              <div className="flex items-center gap-1">
                <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                <span>{m.vote_average.toFixed(1)}</span>
              </div>
              {m.runtime && (
                <div className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  <span>{m.runtime} min</span>
                </div>
              )}
            </div>

            {/* Genres */}
            <div className="flex flex-wrap gap-2 mb-4">
              {genres.map(genre => (
                <span
                  key={genre}
                  className="px-3 py-1 bg-gray-800 text-gray-300 text-sm rounded-full"
                >
                  {genre}
                </span>
              ))}
            </div>

            {/* Overview */}
            <p className="text-gray-300 mb-6">{m.overview}</p>

            {/* WHY RECOMMENDED - The key explainability feature! */}
            <div className="bg-gradient-to-r from-red-900/30 to-transparent border-l-4 border-red-600 p-4 rounded-r-lg mb-6">
              <h3 className="text-lg font-semibold text-white mb-2">
                Why We Recommended This
              </h3>
              <p className="text-gray-300 mb-3">{explanation}</p>
              
              {matchScore && (
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-gray-400 text-sm">Match Score:</span>
                  <div className="flex-1 h-2 bg-gray-700 rounded-full max-w-xs">
                    <div
                      className="h-full bg-red-600 rounded-full"
                      style={{ width: `${matchScore}%` }}
                    />
                  </div>
                  <span className="text-white font-bold">{matchScore}%</span>
                </div>
              )}

              {factors.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {factors.map(factor => (
                    <span
                      key={factor}
                      className="px-2 py-1 bg-red-900/50 text-red-200 text-xs rounded"
                    >
                      {factor}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Quick rating - placeholder for now */}
            <div className="border-t border-gray-800 pt-4">
              <h3 className="text-lg font-semibold text-white mb-3">
                Rate this movie
              </h3>
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                  >
                    <Star className="w-6 h-6 text-gray-600 hover:text-yellow-500 hover:fill-yellow-500" />
                  </button>
                ))}
              </div>
              <p className="text-gray-500 text-sm mt-2">
                Your rating helps improve future recommendations
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}