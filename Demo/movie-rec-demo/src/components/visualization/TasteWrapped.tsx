import { Sparkles } from 'lucide-react';
import { type TasteProfile } from '../../api/visualization';

interface TasteWrappedProps {
  profile: TasteProfile;
  summary: string;
}

export function TasteWrapped({ profile, summary }: TasteWrappedProps) {
  return (
    <div className="bg-gradient-to-br from-red-900/50 to-gray-900 border border-red-800/50 rounded-xl p-6">
      <div className="flex items-center gap-2 mb-4">
        <Sparkles className="w-5 h-5 text-red-400" />
        <h3 className="text-lg font-semibold text-white">Your Taste Wrapped</h3>
      </div>

      {/* Top genres showcase */}
      <div className="flex gap-2 mb-4">
        {profile.topGenres.map((genre, i) => (
          <span
            key={genre}
            className={`px-3 py-1 rounded-full text-sm font-medium ${
              i === 0
                ? 'bg-red-600 text-white'
                : 'bg-gray-800 text-gray-300'
            }`}
          >
            {i === 0 && '🏆 '}
            {genre}
          </span>
        ))}
      </div>

      {/* AI Summary */}
      <p className="text-gray-300 leading-relaxed">{summary}</p>

      {/* Fun stats */}
      <div className="mt-4 pt-4 border-t border-gray-800 grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="text-2xl font-bold text-white">{profile.moviesCount}</p>
          <p className="text-xs text-gray-500">Movies</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-white">{profile.avgRating}</p>
          <p className="text-xs text-gray-500">Avg Rating</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-white">{profile.topGenres.length}</p>
          <p className="text-xs text-gray-500">Top Genres</p>
        </div>
      </div>
    </div>
  );
}