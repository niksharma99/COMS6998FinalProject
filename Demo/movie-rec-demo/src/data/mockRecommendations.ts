import { type Recommendation } from '../types/movie';

// These are real TMDB movie IDs - the API will fetch all the details
// You only need to mock the "AI" parts: which movies and why

export const mockRecommendationSets: Record<string, { title: string; recommendations: Recommendation[] }> = {
  
  // Carousel 1: Based on liking Inception
  "inception-lovers": {
    title: "Because you loved Inception...",
    recommendations: [
      {
        movieId: 1124,      // The Prestige
        explanation: "Complex narrative structure with reality-bending twists, from the same director.",
        matchScore: 95,
        factors: ["director", "narrative complexity", "twist ending"]
      },
      {
        movieId: 157336,    // Interstellar
        explanation: "Epic scope with mind-bending concepts about time and space.",
        matchScore: 92,
        factors: ["director", "sci-fi concepts", "emotional depth"]
      },
      {
        movieId: 27205,     // Inception (for testing, remove later)
        explanation: "You rated this highly - it anchors your taste profile.",
        matchScore: 100,
        factors: ["reference point"]
      },
      {
        movieId: 82992,     // Shutter Island
        explanation: "Psychological thriller with an unreliable reality and a shocking twist.",
        matchScore: 88,
        factors: ["psychological depth", "twist ending", "Leo DiCaprio"]
      },
      {
        movieId: 14836,     // Memento
        explanation: "Non-linear storytelling that challenges your perception, also by Nolan.",
        matchScore: 91,
        factors: ["director", "narrative structure", "mystery"]
      },
    ]
  },

  // Carousel 2: Based on emotional dramas
  "emotional-dramas": {
    title: "For when you want to feel something...",
    recommendations: [
      {
        movieId: 13,        // Forrest Gump
        explanation: "Heartwarming journey through life's ups and downs.",
        matchScore: 89,
        factors: ["emotional depth", "life journey", "Tom Hanks"]
      },
      {
        movieId: 424,       // Schindler's List
        explanation: "Profoundly moving historical drama about humanity in dark times.",
        matchScore: 94,
        factors: ["historical", "emotional impact", "Spielberg"]
      },
      {
        movieId: 489,       // Good Will Hunting
        explanation: "Character study about potential, trauma, and human connection.",
        matchScore: 90,
        factors: ["character-driven", "emotional depth", "psychology"]
      },
      {
        movieId: 550,       // Fight Club
        explanation: "Intense exploration of identity and modern disconnection.",
        matchScore: 85,
        factors: ["psychological", "twist", "social commentary"]
      },
    ]
  },

  // Carousel 3: Hidden gems / unexpected picks
  "hidden-gems": {
    title: "Hidden gems you might have missed...",
    recommendations: [
      {
        movieId: 264660,    // Ex Machina
        explanation: "Intimate sci-fi that questions consciousness and humanity.",
        matchScore: 87,
        factors: ["sci-fi", "philosophical", "tension"]
      },
      {
        movieId: 1422,      // The Departed
        explanation: "Tense crime thriller with incredible performances and twists.",
        matchScore: 88,
        factors: ["crime", "tension", "ensemble cast"]
      },
      {
        movieId: 807,       // Se7en
        explanation: "Dark, atmospheric thriller with unforgettable ending.",
        matchScore: 86,
        factors: ["thriller", "atmosphere", "twist ending"]
      },
      {
        movieId: 680,       // Pulp Fiction
        explanation: "Non-linear storytelling with unforgettable dialogue and style.",
        matchScore: 90,
        factors: ["Tarantino", "dialogue", "structure"]
      },
    ]
  }
};

// Helper to get all recommendations as a flat list
export function getAllMockRecommendations(): Recommendation[] {
  return Object.values(mockRecommendationSets).flatMap(set => set.recommendations);
}

// Helper to get unique movie IDs for batch fetching
export function getAllMockMovieIds(): number[] {
  const ids = getAllMockRecommendations().map(r => r.movieId);
  return [...new Set(ids)];
}
