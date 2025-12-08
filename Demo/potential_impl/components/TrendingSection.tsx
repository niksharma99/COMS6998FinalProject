import { TrendingUp } from 'lucide-react';
import { MovieCard } from './MovieCard';

const trendingMovies = [
  {
    id: 7,
    title: "Velocity Strike",
    rating: 4.5,
    year: 2024,
    genre: "Action",
    image: "https://images.unsplash.com/photo-1645808651017-c5e3018553c7?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhY3Rpb24lMjBtb3ZpZSUyMHNjZW5lfGVufDF8fHx8MTc2NTE2NDY2MXww&ixlib=rb-4.1.0&q=80&w=1080"
  },
  {
    id: 8,
    title: "Shadow Protocol",
    rating: 4.6,
    year: 2024,
    genre: "Thriller",
    image: "https://images.unsplash.com/photo-1595171694538-beb81da39d3e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx0aHJpbGxlciUyMG1vdmllJTIwZGFya3xlbnwxfHx8fDE3NjUxMzY3OTh8MA&ixlib=rb-4.1.0&q=80&w=1080"
  },
  {
    id: 9,
    title: "Stellar Odyssey",
    rating: 4.8,
    year: 2024,
    genre: "Sci-Fi",
    image: "https://images.unsplash.com/photo-1619960535361-0b091a383cd8?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzY2llbmNlJTIwZmljdGlvbiUyMGZ1dHVyaXN0aWN8ZW58MXx8fHwxNzY1MjAxMTM1fDA&ixlib=rb-4.1.0&q=80&w=1080"
  },
  {
    id: 10,
    title: "Cinema Dreams",
    rating: 4.9,
    year: 2024,
    genre: "Drama",
    image: "https://images.unsplash.com/photo-1655367574486-f63675dd69eb?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxjaW5lbWElMjBtb3ZpZSUyMHBvc3RlcnxlbnwxfHx8fDE3NjUxMjM3NjN8MA&ixlib=rb-4.1.0&q=80&w=1080"
  },
  {
    id: 11,
    title: "Hearts in Harmony",
    rating: 4.7,
    year: 2024,
    genre: "Romance",
    image: "https://images.unsplash.com/photo-1708787788824-07d6d97b0111?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxyb21hbnRpYyUyMG1vdmllJTIwY291cGxlfGVufDF8fHx8MTc2NTIwMDg1M3ww&ixlib=rb-4.1.0&q=80&w=1080"
  },
  {
    id: 12,
    title: "Laughter Lines",
    rating: 4.3,
    year: 2024,
    genre: "Comedy",
    image: "https://images.unsplash.com/photo-1604674725989-52c312835516?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxjb21lZHklMjBoYXBweSUyMHBlb3BsZXxlbnwxfHx8fDE3NjUyMDIxNjN8MA&ixlib=rb-4.1.0&q=80&w=1080"
  }
];

export function TrendingSection() {
  return (
    <section className="bg-gray-900 py-16">
      <div className="container mx-auto px-4">
        <div className="flex items-center gap-3 mb-8">
          <TrendingUp className="w-7 h-7 text-red-600" />
          <h2 className="text-white">Trending This Week</h2>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
          {trendingMovies.map((movie) => (
            <MovieCard key={movie.id} movie={movie} />
          ))}
        </div>
      </div>
    </section>
  );
}
