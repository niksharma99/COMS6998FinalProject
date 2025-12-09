import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Film } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { LoginForm } from '../components/auth/LoginForm';
import { SignupForm } from '../components/auth/SignupForm';
import { OAuthButtons } from '../components/auth/OAuthButtons';
import { OnboardingModal } from '../components/onboarding/OnboardingModal';
import { type OnboardingData } from '../types/user';
import { createRequestToken, getAuthorizationUrl } from '../api/tmdbAuth';

export function AuthPage() {
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [showOnboarding, setShowOnboarding] = useState(false);
  const navigate = useNavigate();

  const { login } = useAuth();

  const handleLogin = (email: string, password: string) => {
    console.log('Login:', { email, password });
    login();
    navigate('/');
  };

  const handleSignup = (name: string, email: string, password: string) => {
    // TODO: Implement real authentication
    console.log('Signup:', { name, email, password });
    // After signup, show onboarding
    setShowOnboarding(true);
  };

  const handleOAuthGoogle = () => {
    // TODO: Implement Google OAuth
    console.log('Google OAuth');
    setShowOnboarding(true);
  };

  const handleOAuthTMDB = async () => {
    try {
      // Step 1: Get a request token
      const requestToken = await createRequestToken();
      console.log('TMDB Request Token:', requestToken);

      // Step 2: Redirect to TMDB for user authorization
      const callbackUrl = `${window.location.origin}/auth/tmdb/callback`;
      const authUrl = getAuthorizationUrl(requestToken, callbackUrl);
      
      // Redirect the user to TMDB
      window.location.href = authUrl;
    } catch (error) {
      console.error('TMDB auth error:', error);
      alert('Failed to connect to TMDB. Please try again.');
    }
  };

  const handleOnboardingComplete = async (data: OnboardingData) => {
    console.log('Onboarding complete:', data);
    localStorage.setItem('onboardingData', JSON.stringify(data));
    login();
    navigate('/personalizing');  // Changed from '/'
  };

  const handleOnboardingSkip = () => {
    login();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gray-950 flex">
      {/* Left side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-red-900/20 to-gray-950 items-center justify-center p-12">
        <div className="max-w-md">
          <div className="flex items-center gap-3 mb-8">
            <Film className="w-12 h-12 text-red-600" />
            <span className="text-3xl font-bold text-white">ReelReason</span>
          </div>
          <h1 className="text-4xl font-bold text-white mb-4">
            Discover movies you'll actually love
          </h1>
          <p className="text-gray-400 text-lg">
            Get personalized recommendations powered by AI that understands your unique taste, 
            with explanations for why each movie is perfect for you.
          </p>
        </div>
      </div>

      {/* Right side - Auth forms */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center justify-center gap-2 mb-8">
            <Film className="w-8 h-8 text-red-600" />
            <span className="text-2xl font-bold text-white">ReelReason</span>
          </div>

          {/* Auth card */}
          <div className="bg-gray-900 rounded-2xl p-8">
            <h2 className="text-2xl font-bold text-white mb-2">
              {mode === 'login' ? 'Welcome back' : 'Create an account'}
            </h2>
            <p className="text-gray-400 mb-6">
              {mode === 'login'
                ? 'Sign in to get your personalized recommendations'
                : 'Start your journey to better movie discovery'}
            </p>

            {/* OAuth buttons */}
            <OAuthButtons
              onGoogleClick={handleOAuthGoogle}
              onTMDBClick={handleOAuthTMDB}
            />

            {/* Divider */}
            <div className="flex items-center gap-4 my-6">
              <div className="flex-1 h-px bg-gray-700" />
              <span className="text-gray-500 text-sm">or</span>
              <div className="flex-1 h-px bg-gray-700" />
            </div>

            {/* Form */}
            {mode === 'login' ? (
              <LoginForm
                onSubmit={handleLogin}
                onSwitchToSignup={() => setMode('signup')}
              />
            ) : (
              <SignupForm
                onSubmit={handleSignup}
                onSwitchToLogin={() => setMode('login')}
              />
            )}
          </div>
        </div>
      </div>

      {/* Onboarding modal */}
      {showOnboarding && (
        <OnboardingModal
          onComplete={handleOnboardingComplete}
          onSkip={handleOnboardingSkip}
        />
      )}
    </div>
  );
}