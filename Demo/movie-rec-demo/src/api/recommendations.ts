import { type TMDBMovie } from '../types/movie';
import { getMovie, searchMovies } from './tmdb';

const OPENAI_API_KEY = import.meta.env.VITE_OPENAI_API_KEY;

interface GeneratedRecommendation {
  movieId: number;
  explanation: string;
  matchScore: number;
  factors: string[];
}

interface RecommendationSet {
  title: string;
  recommendations: GeneratedRecommendation[];
}

// Get user's movie data from localStorage
function getUserMovieData(): { 
  ratedMovies: number[]; 
  favoriteMovies: number[];
  recentMovies: number[];
  vibes: string[];
  customVibeText: string;
} {
  // From TMDB OAuth
  const tmdbData = localStorage.getItem('tmdbMovieData');
  const tmdbParsed = tmdbData ? JSON.parse(tmdbData) : { ratedMovies: [], favoriteMovies: [] };

  // From onboarding
  const onboardingData = localStorage.getItem('onboardingData');
  const onboardingParsed = onboardingData ? JSON.parse(onboardingData) : {};

  return {
    ratedMovies: tmdbParsed.ratedMovies || [],
    favoriteMovies: tmdbParsed.favoriteMovies || [],
    recentMovies: onboardingParsed.recentMovies || [],
    vibes: onboardingParsed.selectedVibes || [],
    customVibeText: onboardingParsed.customVibeText || '',
  };
}

// Fetch movie details for a list of IDs
async function getMovieDetails(movieIds: number[]): Promise<TMDBMovie[]> {
  const movies = await Promise.all(
    movieIds.slice(0, 10).map((id) => getMovie(id).catch(() => null))
  );
  return movies.filter((m): m is TMDBMovie => m !== null);
}

// Convert movie title + year to TMDB ID
async function movieTitleToId(title: string, year?: number): Promise<number | null> {
  try {
    const results = await searchMovies(title);
    
    if (results.length === 0) return null;
    
    // If we have a year, try to find exact match
    if (year) {
      const exactMatch = results.find((m) => {
        const movieYear = m.release_date?.split('-')[0];
        return movieYear === year.toString();
      });
      if (exactMatch) return exactMatch.id;
    }
    
    // Otherwise return the first (most relevant) result
    return results[0].id;
  } catch (error) {
    console.error(`Failed to find movie: ${title}`, error);
    return null;
  }
}

// Raw recommendation from OpenAI (before we resolve IDs)
interface RawRecommendation {
  title: string;
  year: number;
  explanation: string;
  matchScore: number;
  factors: string[];
}

interface RawRecommendationSet {
  title: string;
  recommendations: RawRecommendation[];
}

// Call OpenAI to generate recommendations (returns movie titles, not IDs)
async function callOpenAIForRecommendations(
  userMovies: TMDBMovie[],
  vibes: string[],
  customVibeText: string
): Promise<RawRecommendationSet[]> {
  const movieList = userMovies
    .map((m) => `- ${m.title} (${m.release_date?.split('-')[0]})`)
    .join('\n');

  const vibeList = vibes.length > 0 ? vibes.join(', ') : 'not specified';
  const customVibe = customVibeText || 'not provided';

  const prompt = `You are a movie recommendation expert. Based on the user's movie preferences, generate personalized recommendations.

USER'S FAVORITE/RECENTLY WATCHED MOVIES:
${movieList}

USER'S PREFERRED VIBES: ${vibeList}
USER'S CUSTOM DESCRIPTION: ${customVibe}

Generate 3 recommendation categories with 4-5 movies each. Return ONLY valid JSON in this exact format:
{
  "categories": [
    {
      "title": "Because you loved [movie name]...",
      "recommendations": [
        {
          "title": "<exact movie title>",
          "year": <release year as number>,
          "explanation": "<1-2 sentence explanation of why this fits their taste, referencing specific movies they like>",
          "matchScore": <number 75-98>,
          "factors": ["<factor1>", "<factor2>", "<factor3>"]
        }
      ]
    }
  ]
}

Requirements:
- Use EXACT official movie titles (e.g., "The Dark Knight" not "Dark Knight")
- Include the release year to avoid confusion with remakes
- Make explanations personal, referencing their specific movies/vibes by name
- Factors should be things like: "director style", "emotional depth", "plot complexity", "visual style", "ensemble cast", "pacing", "themes", "tone", "humor", "action sequences"
- Category titles should be engaging like "Because you loved Inception...", "For your mind-bending mood...", "Hidden gems you'll appreciate..."
- Match scores should feel realistic (75-98 range)
- Do NOT recommend movies the user has already listed
- Choose movies that are actually similar to what they like

IMPORTANT: Return ONLY the JSON, no markdown, no explanation.`;

  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${OPENAI_API_KEY}`,
    },
    body: JSON.stringify({
      model: 'gpt-4o-mini',
      messages: [
        { role: 'system', content: 'You are a movie recommendation expert. Return only valid JSON.' },
        { role: 'user', content: prompt },
      ],
      max_tokens: 2000,
      temperature: 0.8,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to get recommendations from OpenAI');
  }

  const data = await response.json();
  const content = data.choices[0].message.content;

  // Parse the JSON response
  try {
    const parsed = JSON.parse(content.replace(/```json\n?|\n?```/g, '').trim());
    return parsed.categories;
  } catch (parseError) {
    console.error('Failed to parse OpenAI response:', content);
    throw new Error('Invalid response format from OpenAI');
  }
}

// Convert raw recommendations (with titles) to final recommendations (with IDs)
async function resolveMovieIds(
  rawSets: RawRecommendationSet[]
): Promise<RecommendationSet[]> {
  const resolvedSets: RecommendationSet[] = [];

  for (const rawSet of rawSets) {
    const resolvedRecommendations: GeneratedRecommendation[] = [];

    for (const rec of rawSet.recommendations) {
      const movieId = await movieTitleToId(rec.title, rec.year);
      
      if (movieId) {
        resolvedRecommendations.push({
          movieId,
          explanation: rec.explanation,
          matchScore: rec.matchScore,
          factors: rec.factors,
        });
      } else {
        console.warn(`Could not find movie: ${rec.title} (${rec.year})`);
      }
    }

    // Only add the set if we have at least 2 resolved movies
    if (resolvedRecommendations.length >= 2) {
      resolvedSets.push({
        title: rawSet.title,
        recommendations: resolvedRecommendations,
      });
    }
  }

  return resolvedSets;
}

// Main function to generate and store recommendations
export async function generatePersonalizedRecommendations(): Promise<void> {
  const userData = getUserMovieData();

  // Combine all user movie IDs (from both TMDB and onboarding)
  const allMovieIds = [
    ...userData.favoriteMovies,
    ...userData.recentMovies,
    ...userData.ratedMovies,
  ];

  // Remove duplicates
  const uniqueMovieIds = [...new Set(allMovieIds)];

  console.log('User movie data:', {
    fromTMDB: {
      rated: userData.ratedMovies.length,
      favorites: userData.favoriteMovies.length,
    },
    fromOnboarding: {
      recent: userData.recentMovies.length,
      vibes: userData.vibes,
      customText: userData.customVibeText ? 'yes' : 'no',
    },
    totalUniqueMovies: uniqueMovieIds.length,
  });

  if (uniqueMovieIds.length === 0 && userData.vibes.length === 0 && !userData.customVibeText) {
    console.log('No user movie data found, using defaults');
    return; // Will fall back to mock data
  }

  // Get movie details for the IDs we have
  let movieDetails: TMDBMovie[] = [];
  if (uniqueMovieIds.length > 0) {
    movieDetails = await getMovieDetails(uniqueMovieIds);
  }

  // Even if we don't have movie IDs, we might have vibes from onboarding
  if (movieDetails.length === 0 && (userData.vibes.length === 0 && !userData.customVibeText)) {
    console.log('Could not fetch movie details and no vibes specified');
    return;
  }

  // Generate recommendations via OpenAI (returns titles)
  const rawRecommendations = await callOpenAIForRecommendations(
    movieDetails,
    userData.vibes,
    userData.customVibeText
  );

  console.log('Raw recommendations from OpenAI:', rawRecommendations);

  // Convert movie titles to TMDB IDs
  const recommendations = await resolveMovieIds(rawRecommendations);

  console.log('Resolved recommendations with IDs:', recommendations);

  if (recommendations.length === 0) {
    console.error('Failed to resolve any movie IDs');
    return;
  }

  // Store in localStorage for the home page to use
  localStorage.setItem('personalizedRecommendations', JSON.stringify(recommendations));
  console.log('Generated personalized recommendations:', recommendations);
}

// Get stored recommendations (for HomePage to use)
export function getStoredRecommendations(): RecommendationSet[] | null {
  const stored = localStorage.getItem('personalizedRecommendations');
  if (!stored) return null;
  
  try {
    return JSON.parse(stored);
  } catch {
    return null;
  }
}

// Clear recommendations (for testing/logout)
export function clearRecommendations(): void {
  localStorage.removeItem('personalizedRecommendations');
}