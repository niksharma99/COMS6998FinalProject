import { useMemo } from 'react';
import { type TasteProfile } from '../../api/visualization';

interface TasteMapProps {
  profiles: TasteProfile[];
  selectedProfileId?: string;
  onSelectProfile?: (profile: TasteProfile) => void;
}

export function TasteMap({ profiles, selectedProfileId, onSelectProfile }: TasteMapProps) {
  // Convert -1 to 1 coordinates to pixel positions
  const mapSize = 400;
  const padding = 40;
  
  const getPosition = (x: number, y: number) => ({
    left: padding + ((x + 1) / 2) * (mapSize - padding * 2),
    top: padding + ((1 - y) / 2) * (mapSize - padding * 2), // Invert Y for screen coords
  });

  const userProfile = profiles.find((p) => p.type === 'user');

  return (
    <div className="bg-gray-900 rounded-xl p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Taste Map</h3>
      
      {/* Map container */}
      <div 
        className="relative bg-gray-800 rounded-lg"
        style={{ width: mapSize, height: mapSize }}
      >
        {/* Grid lines */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-px h-full bg-gray-700" />
        </div>
        <div className="absolute inset-0 flex items-center">
          <div className="h-px w-full bg-gray-700" />
        </div>

        {/* Axis labels */}
        <span className="absolute left-2 top-1/2 -translate-y-1/2 text-xs text-gray-500 -rotate-90">
          Light
        </span>
        <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-500 -rotate-90">
          Dark
        </span>
        <span className="absolute bottom-2 left-1/2 -translate-x-1/2 text-xs text-gray-500">
          Mainstream
        </span>
        <span className="absolute top-2 left-1/2 -translate-x-1/2 text-xs text-gray-500">
          Indie
        </span>

        {/* Profile dots */}
        {profiles.map((profile) => {
          const pos = getPosition(profile.coordinates.x, profile.coordinates.y);
          const isUser = profile.type === 'user';
          const isSelected = profile.id === selectedProfileId;
          
          return (
            <button
              key={profile.id}
              onClick={() => onSelectProfile?.(profile)}
              className={`absolute transform -translate-x-1/2 -translate-y-1/2 transition-all ${
                isSelected ? 'scale-125 z-20' : 'hover:scale-110 z-10'
              }`}
              style={{ left: pos.left, top: pos.top }}
              title={profile.name}
            >
              {/* Dot */}
              <div
                className={`rounded-full ${isUser ? 'w-5 h-5' : 'w-4 h-4'} ${
                  isSelected ? 'ring-2 ring-white ring-offset-2 ring-offset-gray-800' : ''
                }`}
                style={{ backgroundColor: profile.color }}
              />
              
              {/* Label */}
              <span 
                className={`absolute left-1/2 -translate-x-1/2 whitespace-nowrap text-xs ${
                  isUser ? 'text-white font-semibold -top-6' : 'text-gray-400 top-5'
                }`}
              >
                {isUser ? 'You' : profile.name}
              </span>
            </button>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 mt-4 justify-center">
        {profiles.map((profile) => (
          <div key={profile.id} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: profile.color }}
            />
            <span className="text-sm text-gray-400">{profile.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}