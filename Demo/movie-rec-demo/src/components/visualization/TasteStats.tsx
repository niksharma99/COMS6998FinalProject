import { Film, Star, TrendingUp, Users } from 'lucide-react';
import { type TasteProfile, calculateSimilarity } from '../../api/visualization';

interface TasteStatsProps {
  profile: TasteProfile;
  comparisonProfiles: TasteProfile[];
}

export function TasteStats({ profile, comparisonProfiles }: TasteStatsProps) {
  const criticProfile = comparisonProfiles.find((p) => p.type === 'critic');
  const avgViewerProfile = comparisonProfiles.find((p) => p.type === 'public');
  
  const criticSimilarity = criticProfile ? calculateSimilarity(profile, criticProfile) : null;
  const avgSimilarity = avgViewerProfile ? calculateSimilarity(profile, avgViewerProfile) : null;

  const stats = [
    {
      icon: Film,
      label: 'Movies Rated',
      value: profile.moviesCount.toString(),
      color: 'text-red-500',
    },
    {
      icon: Star,
      label: 'Average Rating',
      value: `${profile.avgRating}/10`,
      color: 'text-yellow-500',
    },
    {
      icon: TrendingUp,
      label: 'Top Genre',
      value: profile.topGenres[0] || 'N/A',
      color: 'text-green-500',
    },
    {
      icon: Users,
      label: 'Critic Alignment',
      value: criticSimilarity ? `${criticSimilarity}%` : 'N/A',
      color: 'text-blue-500',
    },
  ];

  return (
    <div className="bg-gray-900 rounded-xl p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Your Stats</h3>
      
      <div className="grid grid-cols-2 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-gray-800 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <stat.icon className={`w-4 h-4 ${stat.color}`} />
              <span className="text-gray-400 text-sm">{stat.label}</span>
            </div>
            <p className="text-2xl font-bold text-white">{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Similarity bars */}
      {(criticSimilarity || avgSimilarity) && (
        <div className="mt-6 space-y-3">
          <h4 className="text-sm text-gray-400">Taste Alignment</h4>
          
          {criticSimilarity && (
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-400">vs Critics</span>
                <span className="text-white">{criticSimilarity}%</span>
              </div>
              <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-amber-500 rounded-full transition-all"
                  style={{ width: `${criticSimilarity}%` }}
                />
              </div>
            </div>
          )}
          
          {avgSimilarity && (
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-400">vs Average Viewer</span>
                <span className="text-white">{avgSimilarity}%</span>
              </div>
              <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gray-400 rounded-full transition-all"
                  style={{ width: `${avgSimilarity}%` }}
                />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}