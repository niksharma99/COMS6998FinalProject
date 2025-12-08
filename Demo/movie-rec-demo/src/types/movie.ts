// What we get from TMDB
export interface TMDBMovie {
  id: number;
  title: string;
  overview: string;
  poster_path: string | null;
  backdrop_path: string | null;
  release_date: string;
  vote_average: number;
  genre_ids: number[];
  runtime?: number;
}

// Our recommendation wrapper
export interface Recommendation {
  movieId: number;
  explanation: string;
  matchScore: number;
  factors: string[]; // e.g., ["pacing", "emotional tone", "director style"]
}

// Combined for display
export interface RecommendedMovie {
  movie: TMDBMovie;
  explanation: string;
  matchScore: number;
  factors: string[];
}

// Genre mapping (TMDB uses IDs)
export const GENRE_MAP: Record<number, string> = {
  28: "Action",
  12: "Adventure",
  16: "Animation",
  35: "Comedy",
  80: "Crime",
  99: "Documentary",
  18: "Drama",
  10751: "Family",
  14: "Fantasy",
  36: "History",
  27: "Horror",
  10402: "Music",
  9648: "Mystery",
  10749: "Romance",
  878: "Science Fiction",
  10770: "TV Movie",
  53: "Thriller",
  10752: "War",
  37: "Western",
};