import { Star } from 'lucide-react';

interface Movie {
  id: number;
  title: string;
  rating: number;
  year: number;
  genre: string;
  image: string;
}

interface MovieCardProps {
  movie: Movie;
}

export function MovieCard({ movie }: MovieCardProps) {
  return (
    <div className="group cursor-pointer">
      <div className="relative aspect-[2/3] rounded-lg overflow-hidden mb-3">
        <img
          src={movie.image}
          alt={movie.title}
          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          <div className="absolute bottom-0 left-0 right-0 p-4">
            <div className="flex items-center gap-2 mb-2">
              <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
              <span className="text-white">{movie.rating}</span>
            </div>
          </div>
        </div>
      </div>
      
      <h3 className="text-white mb-1 group-hover:text-red-600 transition-colors">
        {movie.title}
      </h3>
      
      <div className="flex items-center gap-2">
        <span className="text-gray-400">{movie.year}</span>
        <span className="text-gray-600">•</span>
        <span className="text-gray-400">{movie.genre}</span>
      </div>
    </div>
  );
}
