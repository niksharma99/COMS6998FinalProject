import { useMemo } from 'react';
import { type TasteProfile } from '../../api/visualization';

interface GenreRadarProps {
  profile: TasteProfile;
  comparisonProfile?: TasteProfile;
}

const RADAR_GENRES = ['Action', 'Comedy', 'Drama', 'Sci-Fi', 'Thriller', 'Romance', 'Horror', 'Animation'];

export function GenreRadar({ profile, comparisonProfile }: GenreRadarProps) {
  const size = 300;
  const center = size / 2;
  const maxRadius = (size / 2) - 40;

  // Generate points for the radar polygon
  const getPolygonPoints = (genreDistribution: Record<string, number>) => {
    return RADAR_GENRES.map((genre, i) => {
      const angle = (Math.PI * 2 * i) / RADAR_GENRES.length - Math.PI / 2;
      const value = genreDistribution[genre] || 0;
      const radius = (value / 50) * maxRadius; // Normalize to 50% max
      const x = center + radius * Math.cos(angle);
      const y = center + radius * Math.sin(angle);
      return `${x},${y}`;
    }).join(' ');
  };

  // Generate label positions
  const labelPositions = RADAR_GENRES.map((genre, i) => {
    const angle = (Math.PI * 2 * i) / RADAR_GENRES.length - Math.PI / 2;
    const x = center + (maxRadius + 25) * Math.cos(angle);
    const y = center + (maxRadius + 25) * Math.sin(angle);
    return { genre, x, y };
  });

  // Generate grid circles
  const gridCircles = [0.25, 0.5, 0.75, 1].map((ratio) => maxRadius * ratio);

  return (
    <div className="bg-gray-900 rounded-xl p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Genre Preferences</h3>
      
      <svg width={size} height={size} className="mx-auto">
        {/* Grid circles */}
        {gridCircles.map((radius, i) => (
          <circle
            key={i}
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="#374151"
            strokeWidth="1"
          />
        ))}

        {/* Grid lines from center */}
        {RADAR_GENRES.map((_, i) => {
          const angle = (Math.PI * 2 * i) / RADAR_GENRES.length - Math.PI / 2;
          const x2 = center + maxRadius * Math.cos(angle);
          const y2 = center + maxRadius * Math.sin(angle);
          return (
            <line
              key={i}
              x1={center}
              y1={center}
              x2={x2}
              y2={y2}
              stroke="#374151"
              strokeWidth="1"
            />
          );
        })}

        {/* Comparison profile polygon */}
        {comparisonProfile && (
          <polygon
            points={getPolygonPoints(comparisonProfile.genreDistribution)}
            fill={`${comparisonProfile.color}20`}
            stroke={comparisonProfile.color}
            strokeWidth="2"
            strokeDasharray="4"
          />
        )}

        {/* User profile polygon */}
        <polygon
          points={getPolygonPoints(profile.genreDistribution)}
          fill={`${profile.color}30`}
          stroke={profile.color}
          strokeWidth="2"
        />

        {/* Labels */}
        {labelPositions.map(({ genre, x, y }) => (
          <text
            key={genre}
            x={x}
            y={y}
            textAnchor="middle"
            dominantBaseline="middle"
            className="fill-gray-400 text-xs"
          >
            {genre}
          </text>
        ))}
      </svg>

      {/* Legend */}
      {comparisonProfile && (
        <div className="flex justify-center gap-6 mt-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: profile.color }} />
            <span className="text-sm text-gray-400">{profile.name}</span>
          </div>
          <div className="flex items-center gap-2">
            <div 
              className="w-3 h-3 rounded-full border-2 border-dashed" 
              style={{ borderColor: comparisonProfile.color }} 
            />
            <span className="text-sm text-gray-400">{comparisonProfile.name}</span>
          </div>
        </div>
      )}
    </div>
  );
}