import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Clock, MessageSquare, Star, Sparkles } from 'lucide-react';
import { MoviePicker } from '../components/onboarding/MoviePicker';
import { ReviewCard, type Review } from '../components/reviews/ReviewCard';
import { RegenerateModal } from '../components/reviews/RegenerateModal';
import { getMovies } from '../api/tmdb';
import { Spinner } from '../components/ui/Spinner';
import { clearRecommendations } from '../api/recommendations';
import type { TMDBMovie } from '../types/movie';

const STORAGE_KEY = 'userReviews';

export function ReviewsPage() {
  const [selectedMovieIds, setSelectedMovieIds] = useState<number[]>([]);
  const [rating, setRating] = useState(8);
  const [reviewText, setReviewText] = useState('');
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'info'; text: string } | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [movieMap, setMovieMap] = useState<Record<number, TMDBMovie>>({});
  const [isLoadingMovies, setIsLoadingMovies] = useState(false);
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const navigate = useNavigate();

  const selectedMovieId = selectedMovieIds[0] ?? null;

  // Load saved reviews on mount
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

  // Persist reviews to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(reviews));
  }, [reviews]);

  // Fetch movie details for review cards
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

  // Add highly-rated movie to taste profile
  const addToTasteProfile = (movieId: number, rating: number) => {
    if (rating < 8) return; // Only add movies rated 8+

    const onboardingData = JSON.parse(localStorage.getItem('onboardingData') || '{}');
    const favorites = onboardingData.favoriteMovies || [];
    
    // Don't add duplicates
    if (favorites.includes(movieId)) return;
    
    onboardingData.favoriteMovies = [...favorites, movieId];
    localStorage.setItem('onboardingData', JSON.stringify(onboardingData));
    
    console.log(`Added movie ${movieId} to taste profile (rated ${rating}/10)`);
  };

  // Remove from taste profile when review is deleted
  const removeFromTasteProfile = (movieId: number) => {
    const onboardingData = JSON.parse(localStorage.getItem('onboardingData') || '{}');
    if (!onboardingData.favoriteMovies) return;
    
    onboardingData.favoriteMovies = onboardingData.favoriteMovies.filter(
      (id: number) => id !== movieId
    );
    localStorage.setItem('onboardingData', JSON.stringify(onboardingData));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setStatusMessage(null);

    if (!selectedMovieId) {
      setStatusMessage({ type: 'info', text: 'Pick a movie to review first.' });
      return;
    }

    const newReview: Review = {
      movieId: selectedMovieId,
      rating,
      text: reviewText.trim(),
      createdAt: new Date().toISOString(),
    };

    // Save the review
    setReviews((prev) => {
      const filtered = prev.filter((r) => r.movieId !== selectedMovieId);
      return [newReview, ...filtered];
    });

    // Add to taste profile if highly rated
    addToTasteProfile(selectedMovieId, rating);

    // Clear cached recommendations so they'll be regenerated
    clearRecommendations();

    // Get movie name for the message
    const movieName = movieMap[selectedMovieId]?.title || 'This movie';

    // Reset form
    setSelectedMovieIds([]);
    setRating(8);
    setReviewText('');
    
    if (rating >= 8) {
      setStatusMessage({ 
        type: 'success', 
        text: `Review saved! "${movieName}" will appear in your "Because you loved..." recommendations.` 
      });
    } else {
      setStatusMessage({ type: 'success', text: 'Review saved!' });
    }
    
    setTimeout(() => setStatusMessage(null), 4000);
  };

  const handleDelete = (movieId: number) => {
    setReviews((prev) => prev.filter((r) => r.movieId !== movieId));
    removeFromTasteProfile(movieId);
    clearRecommendations();
  };

  const handleRegenerateClick = () => {
    setShowRegenerateModal(true);
  };

  const handleRegenerateComplete = () => {
    setShowRegenerateModal(false);
    setStatusMessage({ 
      type: 'success', 
      text: 'Recommendations updated! Visit the home page to see your new picks.' 
    });
    setTimeout(() => setStatusMessage(null), 4000);
  };

  // Check if user has reviews that could affect recommendations
  const highRatedCount = reviews.filter((r) => r.rating >= 8).length;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col gap-2 mb-8">
        <h1 className="text-3xl font-bold text-white">Your Reviews</h1>
        <p className="text-gray-400">
          Rate movies 8+ to add them to your taste profile and improve recommendations.
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Search + review form */}
        <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Star className="w-5 h-5 text-red-500" />
            <h2 className="text-xl font-semibold text-white">Add a Review</h2>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Movie search */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-400">Search for a movie</p>
              </div>
              <MoviePicker
                selectedIds={selectedMovieIds}
                onChange={setSelectedMovieIds}
                maxSelections={1}
                placeholder="Start typing to search..."
              />
            </div>

            {/* Rating slider */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-400">Your rating</p>
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
              <div className="flex justify-between text-xs text-gray-500">
                <span>Not for me</span>
                <span className={rating >= 8 ? 'text-yellow-500 font-medium' : ''}>
                  {rating >= 8 ? '★ Will influence your recommendations' : ''}
                </span>
                <span>Loved it</span>
              </div>
            </div>

            {/* Review text */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <MessageSquare className="w-4 h-4" />
                <span>What did you think? (optional)</span>
              </div>
              <textarea
                value={reviewText}
                onChange={(e) => setReviewText(e.target.value)}
                rows={4}
                placeholder="Share what you liked, standout moments, or what didn't work..."
                className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white placeholder:text-gray-500 focus:outline-none focus:border-red-500 resize-none"
              />
            </div>

            {/* Status message */}
            {statusMessage && (
              <div className={`text-sm rounded-lg px-3 py-2 ${
                statusMessage.type === 'success' 
                  ? 'text-green-400 bg-green-900/30 border border-green-800' 
                  : 'text-blue-400 bg-blue-900/30 border border-blue-800'
              }`}>
                {statusMessage.text}
              </div>
            )}

            {/* Submit button */}
            <button
              type="submit"
              disabled={!selectedMovieId}
              className="w-full flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white py-3 rounded-lg transition-colors"
            >
              <Star className="w-4 h-4" />
              <span>Save Review</span>
            </button>
          </form>
        </div>

        {/* Review history */}
        <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-red-500" />
              <h2 className="text-xl font-semibold text-white">Review History</h2>
              <span className="text-gray-500 text-sm">({reviews.length})</span>
            </div>
            
            {/* Regenerate button */}
            {highRatedCount > 0 && (
              <button
                onClick={handleRegenerateClick}
                className="flex items-center gap-2 text-sm text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 px-3 py-1.5 rounded-lg transition-colors"
              >
                <Sparkles className="w-4 h-4" />
                <span>Update Recommendations</span>
              </button>
            )}
          </div>

          {/* Loading state */}
          {isLoadingMovies && (
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-4">
              <Spinner className="w-5 h-5" />
              <span>Loading your reviews...</span>
            </div>
          )}

          {/* Empty state */}
          {sortedReviews.length === 0 && !isLoadingMovies && (
            <div className="border border-dashed border-gray-700 rounded-xl p-8 text-center">
              <Star className="w-10 h-10 text-gray-700 mx-auto mb-3" />
              <p className="text-gray-400">No reviews yet</p>
              <p className="text-gray-500 text-sm mt-1">
                Rate movies 8+ to see "Because you loved..." on the home page
              </p>
            </div>
          )}

          {/* Review list */}
          <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
            {sortedReviews.map((review) => (
              <ReviewCard
                key={`${review.movieId}-${review.createdAt}`}
                review={review}
                movie={movieMap[review.movieId]}
                onDelete={handleDelete}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Regenerate Modal */}
      <RegenerateModal
        isOpen={showRegenerateModal}
        onClose={() => setShowRegenerateModal(false)}
        onComplete={handleRegenerateComplete}
      />
    </div>
  );
}