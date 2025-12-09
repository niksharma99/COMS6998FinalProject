import { useEffect, useState } from 'react';
import { Sparkles, RefreshCw } from 'lucide-react';
import { TasteMap } from '../components/visualization/TasteMap';
import { GenreRadar } from '../components/visualization/GenreRadar';
import { TasteStats } from '../components/visualization/TasteStats';
import { TasteWrapped } from '../components/visualization/TasteWrapped';
import { Spinner } from '../components/ui/Spinner';
import {
  type TasteProfile,
  getUserTasteProfile,
  getAverageViewerProfile,
  getCriticProfile,
  getMockFriends,
  generateTasteSummary,
} from '../api/visualization';

export function VisualizationPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [userProfile, setUserProfile] = useState<TasteProfile | null>(null);
  const [comparisonProfiles, setComparisonProfiles] = useState<TasteProfile[]>([]);
  const [selectedComparison, setSelectedComparison] = useState<TasteProfile | null>(null);
  const [summary, setSummary] = useState<string>('');
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);

  useEffect(() => {
    async function loadProfiles() {
      setIsLoading(true);
      try {
        // Load all profiles in parallel
        const [user, avgViewer, critic] = await Promise.all([
          getUserTasteProfile(),
          getAverageViewerProfile(),
          getCriticProfile(),
        ]);

        const friends = getMockFriends();

        if (user) {
          setUserProfile(user);
          
          // Generate AI summary
          setIsGeneratingSummary(true);
          const summaryText = await generateTasteSummary(user);
          setSummary(summaryText);
          setIsGeneratingSummary(false);
        }

        setComparisonProfiles([avgViewer, critic, ...friends]);
      } catch (error) {
        console.error('Failed to load profiles:', error);
      } finally {
        setIsLoading(false);
      }
    }

    loadProfiles();
  }, []);

  const handleSelectProfile = (profile: TasteProfile) => {
    if (profile.type === 'user') {
      setSelectedComparison(null);
    } else {
      setSelectedComparison(profile.id === selectedComparison?.id ? null : profile);
    }
  };

  const handleRefreshSummary = async () => {
    if (!userProfile) return;
    setIsGeneratingSummary(true);
    const summaryText = await generateTasteSummary(userProfile);
    setSummary(summaryText);
    setIsGeneratingSummary(false);
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center py-20">
          <Spinner className="w-10 h-10" />
        </div>
      </div>
    );
  }

  if (!userProfile) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center py-20">
          <Sparkles className="w-16 h-16 text-gray-700 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">No Taste Data Yet</h2>
          <p className="text-gray-400 max-w-md mx-auto">
            Rate some movies or complete the onboarding to see your taste visualization.
          </p>
        </div>
      </div>
    );
  }

  const allProfiles = [userProfile, ...comparisonProfiles];

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Your Taste Wrapped</h1>
        <p className="text-gray-400">
          Discover insights about your movie preferences
        </p>
      </div>

      {/* Main grid */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Left column */}
        <div className="space-y-6">
          {/* Taste Map */}
          <TasteMap
            profiles={allProfiles}
            selectedProfileId={selectedComparison?.id}
            onSelectProfile={handleSelectProfile}
          />

          {/* Stats */}
          <TasteStats
            profile={userProfile}
            comparisonProfiles={comparisonProfiles}
          />
        </div>

        {/* Right column */}
        <div className="space-y-6">
          {/* Genre Radar */}
          <GenreRadar
            profile={userProfile}
            comparisonProfile={selectedComparison || undefined}
          />

          {/* Wrapped Summary */}
          <div className="relative">
            <TasteWrapped
              profile={userProfile}
              summary={isGeneratingSummary ? 'Analyzing your taste...' : summary}
            />
            <button
              onClick={handleRefreshSummary}
              disabled={isGeneratingSummary}
              className="absolute top-4 right-4 p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors disabled:opacity-50"
              title="Generate new summary"
            >
              <RefreshCw className={`w-4 h-4 ${isGeneratingSummary ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Comparison selector hint */}
      <p className="text-center text-gray-500 text-sm mt-8">
        💡 Click on any dot in the Taste Map to compare your genre preferences
      </p>
    </div>
  );
}