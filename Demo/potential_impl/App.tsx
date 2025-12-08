import { Header } from './components/Header';
import { HeroCarousel } from './components/HeroCarousel';
import { FeaturedMovies } from './components/FeaturedMovies';
import { TrendingSection } from './components/TrendingSection';

export default function App() {
  return (
    <div className="min-h-screen bg-gray-950">
      <Header />
      <main>
        <HeroCarousel />
        <FeaturedMovies />
        <TrendingSection />
      </main>
    </div>
  );
}
