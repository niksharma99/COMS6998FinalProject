import { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Star, Play } from 'lucide-react';

const featuredMovies = [
  {
    id: 1,
    title: "Stellar Odyssey",
    description: "An epic journey through uncharted galaxies where humanity's last hope lies in the hands of a brave crew.",
    rating: 4.8,
    year: 2024,
    genre: "Sci-Fi",
    image: "https://images.unsplash.com/photo-1619960535361-0b091a383cd8?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzY2llbmNlJTIwZmljdGlvbiUyMGZ1dHVyaXN0aWN8ZW58MXx8fHwxNzY1MjAxMTM1fDA&ixlib=rb-4.1.0&q=80&w=1080"
  },
  {
    id: 2,
    title: "Shadow Protocol",
    description: "A gripping thriller that keeps you on the edge of your seat as dark secrets unravel in unexpected ways.",
    rating: 4.6,
    year: 2024,
    genre: "Thriller",
    image: "https://images.unsplash.com/photo-1595171694538-beb81da39d3e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx0aHJpbGxlciUyMG1vdmllJTIwZGFya3xlbnwxfHx8fDE3NjUxMzY3OTh8MA&ixlib=rb-4.1.0&q=80&w=1080"
  },
  {
    id: 3,
    title: "Velocity Strike",
    description: "High-octane action meets cutting-edge cinematography in this adrenaline-pumping blockbuster.",
    rating: 4.5,
    year: 2024,
    genre: "Action",
    image: "https://images.unsplash.com/photo-1645808651017-c5e3018553c7?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhY3Rpb24lMjBtb3ZpZSUyMHNjZW5lfGVufDF8fHx8MTc2NTE2NDY2MXww&ixlib=rb-4.1.0&q=80&w=1080"
  },
  {
    id: 4,
    title: "Hearts in Harmony",
    description: "A beautiful love story that explores the depths of human connection and the power of second chances.",
    rating: 4.7,
    year: 2024,
    genre: "Romance",
    image: "https://images.unsplash.com/photo-1708787788824-07d6d97b0111?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxyb21hbnRpYyUyMG1vdmllJTIwY291cGxlfGVufDF8fHx8MTc2NTIwMDg1M3ww&ixlib=rb-4.1.0&q=80&w=1080"
  }
];

export function HeroCarousel() {
  const [currentIndex, setCurrentIndex] = useState(0);
  
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % featuredMovies.length);
    }, 5000);
    
    return () => clearInterval(timer);
  }, []);
  
  const goToPrevious = () => {
    setCurrentIndex((prev) => 
      prev === 0 ? featuredMovies.length - 1 : prev - 1
    );
  };
  
  const goToNext = () => {
    setCurrentIndex((prev) => (prev + 1) % featuredMovies.length);
  };
  
  const currentMovie = featuredMovies[currentIndex];
  
  return (
    <div className="relative h-[600px] overflow-hidden">
      <div 
        className="absolute inset-0 bg-cover bg-center transition-all duration-700"
        style={{ 
          backgroundImage: `url(${currentMovie.image})`,
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-r from-gray-950 via-gray-950/80 to-transparent" />
      </div>
      
      <div className="relative container mx-auto px-4 h-full flex items-center">
        <div className="max-w-2xl">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-red-600 px-3 py-1 bg-red-600/20 rounded-full">
              {currentMovie.genre}
            </span>
            <span className="text-gray-400">
              {currentMovie.year}
            </span>
          </div>
          
          <h1 className="text-white mb-4">
            {currentMovie.title}
          </h1>
          
          <div className="flex items-center gap-2 mb-6">
            <Star className="w-5 h-5 text-yellow-500 fill-yellow-500" />
            <span className="text-white">{currentMovie.rating}</span>
            <span className="text-gray-400">/5.0</span>
          </div>
          
          <p className="text-gray-300 mb-8 max-w-xl">
            {currentMovie.description}
          </p>
          
          <div className="flex gap-4">
            <button className="bg-red-600 hover:bg-red-700 text-white px-8 py-3 rounded-lg flex items-center gap-2 transition-colors">
              <Play className="w-5 h-5" />
              Watch Trailer
            </button>
            <button className="bg-white/10 hover:bg-white/20 text-white px-8 py-3 rounded-lg backdrop-blur-sm transition-colors">
              More Info
            </button>
          </div>
        </div>
      </div>
      
      <button
        onClick={goToPrevious}
        className="absolute left-4 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white p-3 rounded-full backdrop-blur-sm transition-colors"
      >
        <ChevronLeft className="w-6 h-6" />
      </button>
      
      <button
        onClick={goToNext}
        className="absolute right-4 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white p-3 rounded-full backdrop-blur-sm transition-colors"
      >
        <ChevronRight className="w-6 h-6" />
      </button>
      
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex gap-2">
        {featuredMovies.map((_, index) => (
          <button
            key={index}
            onClick={() => setCurrentIndex(index)}
            className={`w-2 h-2 rounded-full transition-all ${
              index === currentIndex 
                ? 'bg-red-600 w-8' 
                : 'bg-white/50 hover:bg-white/70'
            }`}
          />
        ))}
      </div>
    </div>
  );
}
