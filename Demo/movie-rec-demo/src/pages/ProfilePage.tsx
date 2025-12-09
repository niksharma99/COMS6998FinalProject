// src/pages/ProfilePage.tsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  User, 
  Film, 
  Heart, 
  Sparkles, 
  RefreshCw, 
  LogOut, 
  Trash2,
  Check,
  ExternalLink,
  Star,
  Edit3,
  X
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { clearRecommendations } from '../api/recommendations';
import { getMovies } from '../api/tmdb';
import { VIBE_OPTIONS, type OnboardingData } from '../types/user';
import { MoviePicker } from '../components/onboarding/MoviePicker';
import { VibePicker } from '../components/onboarding/VibePicker';
import type { TMDBMovie } from '../types/movie';

interface UserStats {
  reviewsCount: number;
  favoriteMoviesCount: number;
  recentMoviesCount: number;
  vibesCount: number;
}

export function ProfilePage() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  
  // User data
  const [userName, setUserName] = useState<string>('');
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
  const [isTMDBConnected, setIsTMDBConnected] = useState(false);
  
  // Taste profile
  const [favoriteMovies, setFavoriteMovies] = useState<TMDBMovie[]>([]);
  const [recentMovies, setRecentMovies] = useState<TMDBMovie[]>([]);
  const [selectedVibes, setSelectedVibes] = useState<string[]>([]);
  const [customVibeText, setCustomVibeText] = useState('');
  
  // Stats
  const [stats, setStats] = useState<UserStats>({
    reviewsCount: 0,
    favoriteMoviesCount: 0,
    recentMoviesCount: 0,
    vibesCount: 0,
  });
  
  // UI state
  const [isEditingTaste, setIsEditingTaste] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [editFavorites, setEditFavorites] = useState<number[]>([]);
  const [editRecent, setEditRecent] = useState<number[]>([]);
  const [editVibes, setEditVibes] = useState<string[]>([]);
  const [editCustomText, setEditCustomText] = useState('');

  // Load user data on mount
  useEffect(() => {
    // User info
    const user = localStorage.getItem('user');
    if (user) {
      const parsed = JSON.parse(user);
      setUserName(parsed.name || 'User');
      setUserEmail(parsed.email);
      setAvatarUrl(parsed.avatarUrl);
    }
    
    // TMDB connection
    const tmdbSession = localStorage.getItem('tmdbSessionId');
    setIsTMDBConnected(!!tmdbSession);
    
    // Load taste profile
    loadTasteProfile();
    
    // Load stats
    loadStats();
  }, []);

  const loadTasteProfile = async () => {
    const onboardingData = localStorage.getItem('onboardingData');
    const tmdbData = localStorage.getItem('tmdbMovieData');
    
    const onboarding: OnboardingData = onboardingData 
      ? JSON.parse(onboardingData) 
      : { recentMovies: [], favoriteMovies: [], selectedVibes: [], customVibeText: '' };
    const tmdb = tmdbData ? JSON.parse(tmdbData) : { ratedMovies: [], favoriteMovies: [] };
    
    // Combine favorite movies from both sources
    const allFavoriteIds = [...new Set([
      ...(onboarding.favoriteMovies || []),
      ...(tmdb.favoriteMovies || []),
    ])];
    
    const recentIds = onboarding.recentMovies || [];
    
    // Fetch movie details
    if (allFavoriteIds.length > 0) {
      const movies = await getMovies(allFavoriteIds.slice(0, 10));
      setFavoriteMovies(movies);
    }
    
    if (recentIds.length > 0) {
      const movies = await getMovies(recentIds.slice(0, 10));
      setRecentMovies(movies);
    }
    
    setSelectedVibes(onboarding.selectedVibes || []);
    setCustomVibeText(onboarding.customVibeText || '');
  };

  const loadStats = () => {
    const reviews = localStorage.getItem('userReviews');
    const onboardingData = localStorage.getItem('onboardingData');
    const tmdbData = localStorage.getItem('tmdbMovieData');
    
    const reviewsArray = reviews ? JSON.parse(reviews) : [];
    const onboarding = onboardingData ? JSON.parse(onboardingData) : {};
    const tmdb = tmdbData ? JSON.parse(tmdbData) : {};
    
    setStats({
      reviewsCount: reviewsArray.length,
      favoriteMoviesCount: (onboarding.favoriteMovies?.length || 0) + (tmdb.favoriteMovies?.length || 0),
      recentMoviesCount: onboarding.recentMovies?.length || 0,
      vibesCount: onboarding.selectedVibes?.length || 0,
    });
  };

  const handleStartEdit = () => {
    // Initialize edit state with current values
    setEditFavorites(favoriteMovies.map(m => m.id));
    setEditRecent(recentMovies.map(m => m.id));
    setEditVibes(selectedVibes);
    setEditCustomText(customVibeText);
    setIsEditingTaste(true);
  };

  const handleCancelEdit = () => {
    setIsEditingTaste(false);
  };

  const handleSaveEdit = async () => {
    // Update localStorage
    const onboardingData = localStorage.getItem('onboardingData');
    const current = onboardingData ? JSON.parse(onboardingData) : {};
    
    const updated = {
      ...current,
      favoriteMovies: editFavorites,
      recentMovies: editRecent,
      selectedVibes: editVibes,
      customVibeText: editCustomText,
    };
    
    localStorage.setItem('onboardingData', JSON.stringify(updated));
    
    // Reload the display
    await loadTasteProfile();
    loadStats();
    setIsEditingTaste(false);
  };

  const handleRegenerateRecommendations = async () => {
    setIsRegenerating(true);
    clearRecommendations();
    navigate('/personalizing');
  };

  const handleLogout = () => {
    // Clear all user data
    localStorage.removeItem('isAuthenticated');
    localStorage.removeItem('user');
    localStorage.removeItem('onboardingData');
    localStorage.removeItem('tmdbSessionId');
    localStorage.removeItem('tmdbAccount');
    localStorage.removeItem('tmdbMovieData');
    localStorage.removeItem('personalizedRecommendations');
    localStorage.removeItem('userReviews');
    logout();
    navigate('/auth');
  };

  const handleClearData = () => {
    if (confirm('This will clear your taste profile and recommendations. Continue?')) {
      localStorage.removeItem('onboardingData');
      localStorage.removeItem('personalizedRecommendations');
      localStorage.removeItem('userReviews');
      loadTasteProfile();
      loadStats();
    }
  };

  const getVibeLabel = (vibeId: string) => {
    const vibe = VIBE_OPTIONS.find(v => v.id === vibeId);
    return vibe ? `${vibe.emoji} ${vibe.label}` : vibeId;
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-3xl font-bold text-white mb-8">Profile Settings</h1>

      {/* User Info Card */}
      <div className="bg-gray-900 rounded-xl p-6 mb-6">
        <div className="flex items-center gap-4">
          {avatarUrl ? (
            <img 
              src={avatarUrl} 
              alt={userName}
              className="w-16 h-16 rounded-full object-cover"
            />
          ) : (
            <div className="w-16 h-16 rounded-full bg-gray-800 flex items-center justify-center">
              <User className="w-8 h-8 text-gray-400" />
            </div>
          )}
          <div>
            <h2 className="text-xl font-semibold text-white">{userName}</h2>
            {userEmail && (
              <p className="text-gray-400">{userEmail}</p>
            )}
          </div>
        </div>
      </div>

      {/* Connected Accounts */}
      <div className="bg-gray-900 rounded-xl p-6 mb-6">
        <h2 className="text-lg font-semibold text-white mb-4">Connected Accounts</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-[#01d277] rounded-lg flex items-center justify-center">
                <Film className="w-5 h-5 text-white" />
              </div>
              <div>
                <p className="text-white font-medium">TMDB</p>
                <p className="text-sm text-gray-400">The Movie Database</p>
              </div>
            </div>
            {isTMDBConnected ? (
              <span className="flex items-center gap-1 text-green-500 text-sm">
                <Check className="w-4 h-4" />
                Connected
              </span>
            ) : (
              <button 
                onClick={() => navigate('/auth')}
                className="flex items-center gap-1 text-red-500 hover:text-red-400 text-sm"
              >
                Connect
                <ExternalLink className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="bg-gray-900 rounded-xl p-6 mb-6">
        <h2 className="text-lg font-semibold text-white mb-4">Your Stats</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-800 rounded-lg p-4 text-center">
            <Star className="w-6 h-6 text-yellow-500 mx-auto mb-2" />
            <p className="text-2xl font-bold text-white">{stats.reviewsCount}</p>
            <p className="text-sm text-gray-400">Reviews</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 text-center">
            <Heart className="w-6 h-6 text-red-500 mx-auto mb-2" />
            <p className="text-2xl font-bold text-white">{stats.favoriteMoviesCount}</p>
            <p className="text-sm text-gray-400">Favorites</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 text-center">
            <Film className="w-6 h-6 text-blue-500 mx-auto mb-2" />
            <p className="text-2xl font-bold text-white">{stats.recentMoviesCount}</p>
            <p className="text-sm text-gray-400">Recent</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 text-center">
            <Sparkles className="w-6 h-6 text-purple-500 mx-auto mb-2" />
            <p className="text-2xl font-bold text-white">{stats.vibesCount}</p>
            <p className="text-sm text-gray-400">Vibes</p>
          </div>
        </div>
      </div>

      {/* Taste Profile */}
      <div className="bg-gray-900 rounded-xl p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Taste Profile</h2>
          {!isEditingTaste ? (
            <button
              onClick={handleStartEdit}
              className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
            >
              <Edit3 className="w-4 h-4" />
              Edit
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <button
                onClick={handleCancelEdit}
                className="flex items-center gap-1 text-gray-400 hover:text-white transition-colors px-3 py-1"
              >
                <X className="w-4 h-4" />
                Cancel
              </button>
              <button
                onClick={handleSaveEdit}
                className="flex items-center gap-1 bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded-lg transition-colors"
              >
                <Check className="w-4 h-4" />
                Save
              </button>
            </div>
          )}
        </div>

        {!isEditingTaste ? (
          // Display mode
          <div className="space-y-6">
            {/* Favorite Movies */}
            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-3">Favorite Movies</h3>
              {favoriteMovies.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {favoriteMovies.map((movie) => (
                    <div
                      key={movie.id}
                      className="flex items-center gap-2 bg-gray-800 rounded-lg px-3 py-2"
                    >
                      {movie.poster_path && (
                        <img
                          src={`https://image.tmdb.org/t/p/w92${movie.poster_path}`}
                          alt={movie.title}
                          className="w-8 h-12 rounded object-cover"
                        />
                      )}
                      <span className="text-white text-sm">{movie.title}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">No favorites added yet</p>
              )}
            </div>

            {/* Recently Watched */}
            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-3">Recently Watched</h3>
              {recentMovies.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {recentMovies.map((movie) => (
                    <div
                      key={movie.id}
                      className="flex items-center gap-2 bg-gray-800 rounded-lg px-3 py-2"
                    >
                      {movie.poster_path && (
                        <img
                          src={`https://image.tmdb.org/t/p/w92${movie.poster_path}`}
                          alt={movie.title}
                          className="w-8 h-12 rounded object-cover"
                        />
                      )}
                      <span className="text-white text-sm">{movie.title}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">No recent movies added</p>
              )}
            </div>

            {/* Vibes */}
            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-3">Your Vibes</h3>
              {selectedVibes.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {selectedVibes.map((vibeId) => (
                    <span
                      key={vibeId}
                      className="bg-red-600/20 text-red-400 px-3 py-1 rounded-full text-sm"
                    >
                      {getVibeLabel(vibeId)}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">No vibes selected</p>
              )}
              {customVibeText && (
                <div className="mt-3 p-3 bg-gray-800 rounded-lg">
                  <p className="text-sm text-gray-400 mb-1">Custom description:</p>
                  <p className="text-white text-sm">{customVibeText}</p>
                </div>
              )}
            </div>
          </div>
        ) : (
          // Edit mode
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-3">Favorite Movies</h3>
              <MoviePicker
                selectedIds={editFavorites}
                onChange={setEditFavorites}
                maxSelections={10}
                placeholder="Search for your favorites..."
              />
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-3">Recently Watched</h3>
              <MoviePicker
                selectedIds={editRecent}
                onChange={setEditRecent}
                maxSelections={8}
                placeholder="Search for recent movies..."
              />
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-3">Your Vibes</h3>
              <VibePicker
                selectedVibes={editVibes}
                customText={editCustomText}
                onVibesChange={setEditVibes}
                onCustomTextChange={setEditCustomText}
              />
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="bg-gray-900 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Actions</h2>
        <div className="space-y-3">
          <button
            onClick={handleRegenerateRecommendations}
            disabled={isRegenerating}
            className="w-full flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 text-white py-3 px-4 rounded-lg transition-colors"
          >
            <RefreshCw className={`w-5 h-5 ${isRegenerating ? 'animate-spin' : ''}`} />
            Regenerate Recommendations
          </button>
          
          <button
            onClick={handleClearData}
            className="w-full flex items-center justify-center gap-2 bg-gray-800 hover:bg-gray-700 text-gray-300 py-3 px-4 rounded-lg transition-colors"
          >
            <Trash2 className="w-5 h-5" />
            Clear Taste Profile
          </button>
          
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 bg-gray-800 hover:bg-red-900 text-gray-300 hover:text-red-400 py-3 px-4 rounded-lg transition-colors"
          >
            <LogOut className="w-5 h-5" />
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}