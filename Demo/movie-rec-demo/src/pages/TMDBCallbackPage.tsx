import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Film } from 'lucide-react';
import { Spinner } from '../components/ui/Spinner';
import { createSession, getAccountDetails, getRatedMovies, getFavoriteMovies } from '../api/tmdbAuth';
import { useAuth } from '../context/AuthContext';

export function TMDBCallbackPage() {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [error, setError] = useState<string>('');
  const navigate = useNavigate();
  const { login } = useAuth();

  useEffect(() => {
    // Check params immediately before async work
    const requestToken = searchParams.get('request_token');
    const approved = searchParams.get('approved');
    const denied = searchParams.get('denied');

    // If denied or missing params, show error immediately
    if (denied === 'true') {
      setStatus('error');
      setError('Authorization was denied');
      return;
    }

    if (!requestToken) {
      setStatus('error');
      setError('Missing request token');
      return;
    }

    // Note: TMDB doesn't always send approved=true, sometimes it just redirects back
    // So we should try to create the session regardless

    async function handleCallback() {
      try {
        // Step 3: Create session with the authorized token
        const sessionId = await createSession(requestToken!);
        console.log('TMDB Session ID:', sessionId);

        // Get user account details
        const account = await getAccountDetails(sessionId);
        console.log('TMDB Account:', account);

        // Get user's movie data (rated + favorites)
        const [ratedMovies, favoriteMovies] = await Promise.all([
          getRatedMovies(account.id, sessionId),
          getFavoriteMovies(account.id, sessionId),
        ]);

        console.log('Rated movies:', ratedMovies);
        console.log('Favorite movies:', favoriteMovies);

        // Store TMDB data
        localStorage.setItem('tmdbSessionId', sessionId);
        localStorage.setItem('tmdbAccount', JSON.stringify(account));
        localStorage.setItem('user', JSON.stringify({
          id: `tmdb_${account.id}`,
          name: account.username || account.name || 'TMDB User',
          email: null,
          avatarUrl: account.avatar?.tmdb?.avatar_path 
            ? `https://image.tmdb.org/t/p/w200${account.avatar.tmdb.avatar_path}`
            : account.avatar?.gravatar?.hash
              ? `https://www.gravatar.com/avatar/${account.avatar.gravatar.hash}`
              : null,
        }));

        // Store their movie data for onboarding pre-fill
        const tmdbMovieData = {
          ratedMovies: ratedMovies.results?.map((m: any) => m.id) || [],
          favoriteMovies: favoriteMovies.results?.map((m: any) => m.id) || [],
        };
        localStorage.setItem('tmdbMovieData', JSON.stringify(tmdbMovieData));

        // Log in the user
        login();
        
        setStatus('success');

        // Redirect after a short delay to show success
        setTimeout(() => {
        // If user has enough movie data, go to personalizing page
        const hasEnoughData = 
            (ratedMovies.results?.length || 0) >= 5 || 
            (favoriteMovies.results?.length || 0) >= 3;

        if (hasEnoughData) {
            navigate('/personalizing');
        } else {
            // Not enough TMDB data, go to home for onboarding
            navigate('/');
        }
        }, 1500);

      } catch (err) {
        console.error('TMDB auth error:', err);
        setStatus('error');
        setError(err instanceof Error ? err.message : 'Authentication failed');
      }
    }

    handleCallback();
  }, [searchParams, navigate, login]);

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="text-center">
        <div className="flex items-center justify-center gap-2 mb-6">
          <Film className="w-10 h-10 text-red-600" />
          <span className="text-2xl font-bold text-white">ReelReason</span>
        </div>

        {status === 'loading' && (
          <>
            <Spinner className="w-10 h-10 mx-auto mb-4" />
            <p className="text-white text-lg">Connecting your TMDB account...</p>
            <p className="text-gray-400 text-sm mt-2">Importing your movie data</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="w-16 h-16 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="text-white text-lg">Connected successfully!</p>
            <p className="text-gray-400 text-sm mt-2">Redirecting you now...</p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="w-16 h-16 bg-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <p className="text-white text-lg">Connection failed</p>
            <p className="text-red-400 text-sm mt-2">{error}</p>
            <button
              onClick={() => navigate('/auth')}
              className="mt-4 bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg"
            >
              Back to Sign In
            </button>
          </>
        )}
      </div>
    </div>
  );
}