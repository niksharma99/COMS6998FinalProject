import type { TMDBMovie } from '../types/movie';

const API_KEY = import.meta.env.VITE_TMDB_API_KEY;
const BASE_URL = 'https://api.themoviedb.org/3';
const IMAGE_BASE_URL = 'https://image.tmdb.org/t/p';

// Helper to build image URLs
export function getPosterUrl(path: string | null, size: 'w200' | 'w300' | 'w500' | 'original' = 'w300'): string {
  if (!path) return '/placeholder-poster.jpg';
  return `${IMAGE_BASE_URL}/${size}${path}`;
}

export function getBackdropUrl(path: string | null, size: 'w780' | 'w1280' | 'original' = 'w1280'): string {
  if (!path) return '';
  return `${IMAGE_BASE_URL}/${size}${path}`;
}

// Fetch a single movie by ID
export async function getMovie(movieId: number): Promise<TMDBMovie> {
  const response = await fetch(
    `${BASE_URL}/movie/${movieId}?api_key=${API_KEY}`
  );
  
  if (!response.ok) {
    throw new Error(`Failed to fetch movie ${movieId}`);
  }
  
  return response.json();
}

// Fetch multiple movies by IDs
export async function getMovies(movieIds: number[]): Promise<TMDBMovie[]> {
  const movies = await Promise.all(
    movieIds.map(id => getMovie(id).catch(() => null))
  );
  return movies.filter((m): m is TMDBMovie => m !== null);
}

// Search movies by title (useful for the review page)
export async function searchMovies(query: string): Promise<TMDBMovie[]> {
  if (!query.trim()) return [];
  
  const response = await fetch(
    `${BASE_URL}/search/movie?api_key=${API_KEY}&query=${encodeURIComponent(query)}`
  );
  
  if (!response.ok) {
    throw new Error('Search failed');
  }
  
  const data = await response.json();
  return data.results;
}

// Get popular movies (good for fallback/browse)
export async function getPopularMovies(): Promise<TMDBMovie[]> {
  const response = await fetch(
    `${BASE_URL}/movie/popular?api_key=${API_KEY}`
  );
  
  if (!response.ok) {
    throw new Error('Failed to fetch popular movies');
  }
  
  const data = await response.json();
  return data.results;
}