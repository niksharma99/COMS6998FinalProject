import { useEffect, useMemo, useState } from 'react';
import { Clock, MessageSquare, Star } from 'lucide-react';
import { MoviePicker } from '../components/onboarding/MoviePicker';
import { getMovies, getPosterUrl } from '../api/tmdb';
import { Spinner } from '../components/ui/Spinner';
import type { TMDBMovie } from '../types/movie';

interface Review {
  movieId: number;
  rating: number;
  text: string;
  createdAt: string;
}

const STORAGE_KEY = 'userReviews';

function formatDate(date: string) {
  return new Date(date).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export function ReviewsPage() {
  const [selectedMovieIds, setSelectedMovieIds] = useState<number[]>([]);
  const [rating, setRating] = useState(8);
  const [reviewText, setReviewText] = useState('');
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [movieMap, setMovieMap] = useState<Record<number, TMDBMovie>>({});
  const [isLoadingMovies, setIsLoadingMovies] = useState(false);

  const selectedMovieId = selectedMovieIds[0] ?? null;

  // Load saved reviews
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return;
    try {
      const parsed: Review[] = JSON.parse(stored);
      setReviews(parsed);
    } catch {
      setReviews([]);
    }
  }, []);

  // Persist reviews
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(reviews));
  }, [reviews]);

  // Fetch movie details for history cards
  useEffect(() => {
    const ids = Array.from(new Set(reviews.map((r) => r.movieId)));
    if (ids.length === 0) {
      setMovieMap({});
      return;
    }

    let isMounted = true;
    setIsLoadingMovies(true);
    getMovies(ids)
      .then((movies) => {
        if (!isMounted) return;
        const map: Record<number, TMDBMovie> = {};
        movies.forEach((movie) => {
          map[movie.id] = movie;
        });
        setMovieMap(map);
      })
      .catch(() => {
        if (isMounted) setMovieMap({});
      })
      .finally(() => {
        if (isMounted) setIsLoadingMovies(false);
      });

    return () => {
      isMounted = false;
    };
  }, [reviews]);

  const sortedReviews = useMemo(
    () => [...reviews].sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()),
    [reviews]
  );

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setStatusMessage(null);

    if (!selectedMovieId) {
      setStatusMessage('Pick a movie to review first.');
      return;
    }

    const newReview: Review = {
      movieId: selectedMovieId,
      rating,
      text: reviewText.trim(),
      createdAt: new Date().toISOString(),
    };

    setReviews((prev) => {
      // Replace any existing review for this movie
      const filtered = prev.filter((r) => r.movieId !== selectedMovieId);
      return [newReview, ...filtered];
    });

    setSelectedMovieIds([]);
    setRating(8);
    setReviewText('');
    setStatusMessage('Saved! Your review was added to history.');
    setTimeout(() => setStatusMessage(null), 2000);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col gap-2 mb-8">
        <h1 className="text-3xl font-bold text-white">Your Reviews</h1>
        <p className="text-gray-400">
          Rate and review movies to sharpen your recommendations.
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Search + review form */}
        <div className="bg-gray-950 border border-gray-900 rounded-2xl p-6 shadow-xl shadow-red-900/10">
          <div className="flex items-center gap-2 mb-4">
            <Star className="w-5 h-5 text-red-500" />
            <h2 className="text-xl font-semibold text-white">Add a review</h2>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-400">Movie search</p>
                <span className="text-xs text-gray-500">Powered by TMDB</span>
              </div>
              <MoviePicker
                selectedIds={selectedMovieIds}
                onChange={setSelectedMovieIds}
                maxSelections={1}
                placeholder="Start typing to search for a movie..."
              />
            </div>

            {selectedMovieId && (
              <div className="flex items-center gap-2 text-sm text-gray-300 bg-gray-900 border border-gray-800 rounded-lg px-3 py-2">
                <span className="text-gray-500">Selected:</span>
                <span className="font-medium">
                  {movieMap[selectedMovieId]?.title || 'Movie selected'}
                </span>
              </div>
            )}

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-400">Rating</p>
                <div className="flex items-center gap-2">
                  <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                  <span className="text-white font-semibold">{rating}/10</span>
                </div>
              </div>
              <input
                type="range"
                min={1}
                max={10}
                step={1}
                value={rating}
                onChange={(e) => setRating(Number(e.target.value))}
                className="w-full accent-red-600"
              />
              <p className="text-xs text-gray-500">
                Slide to set your score. 10 = loved it, 1 = hard pass.
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <MessageSquare className="w-4 h-4" />
                <span>What did you think?</span>
              </div>
              <textarea
                value={reviewText}
                onChange={(e) => setReviewText(e.target.value)}
                rows={5}
                placeholder="Share the vibes, standout moments, or what missed the mark..."
                className="w-full bg-gray-900 border border-gray-800 rounded-lg p-3 text-white placeholder:text-gray-500 focus:outline-none focus:border-red-500"
              />
            </div>

            {statusMessage && (
              <div className="text-sm text-green-400 bg-green-900/30 border border-green-800 rounded-lg px-3 py-2">
                {statusMessage}
              </div>
            )}

            <div className="flex justify-end">
              <button
                type="submit"
                className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white px-4 py-3 rounded-lg transition-colors disabled:opacity-50"
              >
                <Star className="w-4 h-4" />
                <span>Save review</span>
              </button>
            </div>
          </form>
        </div>

        {/* Review history */}
        <div className="bg-gray-950 border border-gray-900 rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="w-5 h-5 text-red-500" />
            <h2 className="text-xl font-semibold text-white">Review history</h2>
          </div>

          {isLoadingMovies && (
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-4">
              <Spinner className="w-5 h-5" />
              <span>Loading your reviews...</span>
            </div>
          )}

          {sortedReviews.length === 0 && !isLoadingMovies && (
            <div className="border border-dashed border-gray-800 rounded-xl p-8 text-center">
              <p className="text-gray-400">No reviews yet.</p>
              <p className="text-gray-500 text-sm mt-2">Search for a movie and leave your first review.</p>
            </div>
          )}

          <div className="space-y-4">
            {sortedReviews.map((review) => {
              const movie = movieMap[review.movieId];
              return (
                <div
                  key={`${review.movieId}-${review.createdAt}`}
                  className="flex gap-4 bg-gray-900 border border-gray-800 rounded-xl p-4"
                >
                  {movie ? (
                    <img
                      src={getPosterUrl(movie.poster_path, 'w200')}
                      alt={movie.title}
                      className="w-16 h-24 object-cover rounded-lg"
                    />
                  ) : (
                    <div className="w-16 h-24 bg-gray-800 rounded-lg" />
                  )}

                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="text-white font-semibold leading-tight">
                          {movie ? movie.title : 'Movie'}
                        </h3>
                        {movie && (
                          <p className="text-gray-500 text-sm">
                            {movie.release_date?.split('-')[0] || 'Year TBA'}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-2 bg-gray-800 rounded-full px-3 py-1">
                        <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                        <span className="text-white font-semibold text-sm">{review.rating}/10</span>
                      </div>
                    </div>

                    {review.text && (
                      <p className="text-gray-300 text-sm mt-3 whitespace-pre-line">
                        {review.text}
                      </p>
                    )}

                    <div className="flex items-center gap-2 text-xs text-gray-500 mt-3">
                      <Clock className="w-4 h-4" />
                      <span>{formatDate(review.createdAt)}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
