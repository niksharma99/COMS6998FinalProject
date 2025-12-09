import { getMovie, getPopularMovies } from './tmdb';
import { type TMDBMovie, GENRE_MAP } from '../types/movie';

const OPENAI_API_KEY = import.meta.env.VITE_OPENAI_API_KEY;

// Calculate genre distribution from a list of movies
export function calculateGenreDistribution(movies: TMDBMovie[]): Record<string, number> {
  const genreCounts: Record<string, number> = {};
  let totalGenres = 0;

  movies.forEach((movie) => {
    movie.genre_ids?.forEach((genreId) => {
      const genreName = GENRE_MAP[genreId];
      if (genreName) {
        genreCounts[genreName] = (genreCounts[genreName] || 0) + 1;
        totalGenres++;
      }
    });
  });

  // Convert to percentages
  const distribution: Record<string, number> = {};
  Object.entries(genreCounts).forEach(([genre, count]) => {
    distribution[genre] = Math.round((count / totalGenres) * 100);
  });

  return distribution;
}

// Generate 2D coordinates from genre distribution (simplified "embedding")
export function generateTasteCoordinates(genreDistribution: Record<string, number>): { x: number; y: number } {
  // X-axis: Mainstream vs Indie
  // Mainstream = Action, Comedy, Adventure, Animation
  // Indie = Drama, Documentary, Foreign, Independent
  const mainstreamGenres = ['Action', 'Comedy', 'Adventure', 'Animation', 'Family'];
  const indieGenres = ['Drama', 'Documentary', 'History', 'War'];
  
  let mainstreamScore = 0;
  let indieScore = 0;
  
  mainstreamGenres.forEach((g) => { mainstreamScore += genreDistribution[g] || 0; });
  indieGenres.forEach((g) => { indieScore += genreDistribution[g] || 0; });
  
  const x = (mainstreamScore - indieScore) / 100; // -1 to 1

  // Y-axis: Light vs Dark
  // Light = Comedy, Romance, Family, Animation
  // Dark = Horror, Thriller, Crime, Mystery
  const lightGenres = ['Comedy', 'Romance', 'Family', 'Animation', 'Music'];
  const darkGenres = ['Horror', 'Thriller', 'Crime', 'Mystery', 'War'];
  
  let lightScore = 0;
  let darkScore = 0;
  
  lightGenres.forEach((g) => { lightScore += genreDistribution[g] || 0; });
  darkGenres.forEach((g) => { darkScore += genreDistribution[g] || 0; });
  
  const y = (lightScore - darkScore) / 100; // -1 to 1

  return { x, y };
}

// Mock comparison profiles
export interface TasteProfile {
  id: string;
  name: string;
  type: 'user' | 'friend' | 'public' | 'critic';
  coordinates: { x: number; y: number };
  genreDistribution: Record<string, number>;
  moviesCount: number;
  avgRating: number;
  topGenres: string[];
  color: string;
}

// Generate mock friend profiles for demo
export function getMockFriends(): TasteProfile[] {
  return [
    {
      id: 'friend-alex',
      name: 'Alex',
      type: 'friend',
      coordinates: { x: 0.3, y: 0.2 },
      genreDistribution: { 'Action': 30, 'Sci-Fi': 25, 'Thriller': 20, 'Comedy': 15, 'Drama': 10 },
      moviesCount: 89,
      avgRating: 7.2,
      topGenres: ['Action', 'Sci-Fi', 'Thriller'],
      color: '#3B82F6', // blue
    },
    {
      id: 'friend-jordan',
      name: 'Jordan',
      type: 'friend',
      coordinates: { x: -0.4, y: 0.5 },
      genreDistribution: { 'Comedy': 35, 'Romance': 25, 'Drama': 20, 'Animation': 15, 'Family': 5 },
      moviesCount: 156,
      avgRating: 8.1,
      topGenres: ['Comedy', 'Romance', 'Drama'],
      color: '#10B981', // green
    },
    {
      id: 'friend-sam',
      name: 'Sam',
      type: 'friend',
      coordinates: { x: -0.2, y: -0.6 },
      genreDistribution: { 'Horror': 30, 'Thriller': 25, 'Mystery': 20, 'Crime': 15, 'Drama': 10 },
      moviesCount: 67,
      avgRating: 6.8,
      topGenres: ['Horror', 'Thriller', 'Mystery'],
      color: '#8B5CF6', // purple
    },
  ];
}

// Generate "average viewer" profile from TMDB popular movies
export async function getAverageViewerProfile(): Promise<TasteProfile> {
  try {
    const popular = await getPopularMovies();
    const genreDistribution = calculateGenreDistribution(popular);
    const coordinates = generateTasteCoordinates(genreDistribution);
    const topGenres = Object.entries(genreDistribution)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([genre]) => genre);

    return {
      id: 'average-viewer',
      name: 'Average Viewer',
      type: 'public',
      coordinates,
      genreDistribution,
      moviesCount: 0,
      avgRating: 7.0,
      topGenres,
      color: '#6B7280', // gray
    };
  } catch (error) {
    // Fallback mock data
    return {
      id: 'average-viewer',
      name: 'Average Viewer',
      type: 'public',
      coordinates: { x: 0.2, y: 0.1 },
      genreDistribution: { 'Action': 25, 'Comedy': 20, 'Drama': 18, 'Adventure': 15, 'Thriller': 12, 'Sci-Fi': 10 },
      moviesCount: 0,
      avgRating: 7.0,
      topGenres: ['Action', 'Comedy', 'Drama'],
      color: '#6B7280',
    };
  }
}

// Generate "critic consensus" profile from TMDB top-rated movies
export async function getCriticProfile(): Promise<TasteProfile> {
  try {
    const response = await fetch(
      `https://api.themoviedb.org/3/movie/top_rated?api_key=${import.meta.env.VITE_TMDB_API_KEY}`
    );
    const data = await response.json();
    const topRated: TMDBMovie[] = data.results || [];
    
    const genreDistribution = calculateGenreDistribution(topRated);
    const coordinates = generateTasteCoordinates(genreDistribution);
    const topGenres = Object.entries(genreDistribution)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([genre]) => genre);

    return {
      id: 'critic-consensus',
      name: 'Critic Consensus',
      type: 'critic',
      coordinates,
      genreDistribution,
      moviesCount: 0,
      avgRating: 8.5,
      topGenres,
      color: '#F59E0B', // amber
    };
  } catch (error) {
    return {
      id: 'critic-consensus',
      name: 'Critic Consensus',
      type: 'critic',
      coordinates: { x: -0.3, y: -0.1 },
      genreDistribution: { 'Drama': 35, 'Crime': 15, 'History': 12, 'War': 10, 'Thriller': 10, 'Romance': 8 },
      moviesCount: 0,
      avgRating: 8.5,
      topGenres: ['Drama', 'Crime', 'History'],
      color: '#F59E0B',
    };
  }
}

// Generate user's taste profile from their data
export async function getUserTasteProfile(): Promise<TasteProfile | null> {
  // Get user's movie IDs from all sources
  const onboardingData = JSON.parse(localStorage.getItem('onboardingData') || '{}');
  const tmdbData = JSON.parse(localStorage.getItem('tmdbMovieData') || '{}');
  const reviews = JSON.parse(localStorage.getItem('userReviews') || '[]');

  const allMovieIds = [
    ...(onboardingData.favoriteMovies || []),
    ...(onboardingData.recentMovies || []),
    ...(tmdbData.ratedMovies || []),
    ...(tmdbData.favoriteMovies || []),
    ...reviews.map((r: any) => r.movieId),
  ];

  const uniqueIds = [...new Set(allMovieIds)];

  if (uniqueIds.length === 0) {
    return null;
  }

  // Fetch movie details
  const movies = await Promise.all(
    uniqueIds.slice(0, 50).map((id) => getMovie(id).catch(() => null))
  );
  const validMovies = movies.filter((m): m is TMDBMovie => m !== null);

  if (validMovies.length === 0) {
    return null;
  }

  const genreDistribution = calculateGenreDistribution(validMovies);
  const coordinates = generateTasteCoordinates(genreDistribution);
  const topGenres = Object.entries(genreDistribution)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([genre]) => genre);

  // Calculate average rating from reviews
  const avgRating = reviews.length > 0
    ? reviews.reduce((sum: number, r: any) => sum + r.rating, 0) / reviews.length
    : 7.5;

  const user = JSON.parse(localStorage.getItem('user') || '{}');

  return {
    id: 'user',
    name: user.name || 'You',
    type: 'user',
    coordinates,
    genreDistribution,
    moviesCount: uniqueIds.length,
    avgRating: Math.round(avgRating * 10) / 10,
    topGenres,
    color: '#EF4444', // red
  };
}

// Calculate similarity between two profiles (0-100)
export function calculateSimilarity(profile1: TasteProfile, profile2: TasteProfile): number {
  // Euclidean distance in 2D space, converted to similarity percentage
  const dx = profile1.coordinates.x - profile2.coordinates.x;
  const dy = profile1.coordinates.y - profile2.coordinates.y;
  const distance = Math.sqrt(dx * dx + dy * dy);
  
  // Max possible distance is ~2.83 (corner to corner of -1 to 1 square)
  const maxDistance = 2.83;
  const similarity = Math.round((1 - distance / maxDistance) * 100);
  
  return Math.max(0, Math.min(100, similarity));
}

// Generate AI summary of user's taste
export async function generateTasteSummary(profile: TasteProfile): Promise<string> {
  const prompt = `Based on this movie taste profile, write a 2-3 sentence personalized "Taste Wrapped" summary in second person ("You..."). Be specific and insightful.

Profile:
- Top genres: ${profile.topGenres.join(', ')}
- Genre distribution: ${JSON.stringify(profile.genreDistribution)}
- Movies rated: ${profile.moviesCount}
- Average rating: ${profile.avgRating}/10
- Position on taste map: ${profile.coordinates.x > 0 ? 'leans mainstream' : 'leans indie'}, ${profile.coordinates.y > 0 ? 'prefers lighter fare' : 'enjoys darker themes'}

Write a fun, insightful summary like Spotify Wrapped would. Be specific about their taste patterns.`;

  try {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        messages: [
          { role: 'system', content: 'You write fun, insightful movie taste summaries like Spotify Wrapped.' },
          { role: 'user', content: prompt },
        ],
        max_tokens: 200,
        temperature: 0.8,
      }),
    });

    const data = await response.json();
    return data.choices[0].message.content;
  } catch (error) {
    return `You've explored ${profile.moviesCount} movies with a love for ${profile.topGenres.slice(0, 2).join(' and ')}. Your ${profile.avgRating >= 8 ? 'generous' : 'discerning'} ratings suggest you know exactly what you like.`;
  }
}