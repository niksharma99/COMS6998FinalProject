import { Film, Search, User } from 'lucide-react';

export function Header() {
  return (
    <header className="bg-gray-950 border-b border-gray-800 sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Film className="w-8 h-8 text-red-600" />
            <span className="text-white">MovieHub</span>
          </div>
          
          <nav className="hidden md:flex items-center gap-8">
            <a href="#" className="text-gray-300 hover:text-white transition-colors">
              Home
            </a>
            <a href="#" className="text-gray-300 hover:text-white transition-colors">
              Movies
            </a>
            <a href="#" className="text-gray-300 hover:text-white transition-colors">
              Reviews
            </a>
            <a href="#" className="text-gray-300 hover:text-white transition-colors">
              Top Rated
            </a>
          </nav>
          
          <div className="flex items-center gap-4">
            <button className="text-gray-300 hover:text-white transition-colors">
              <Search className="w-5 h-5" />
            </button>
            <button className="text-gray-300 hover:text-white transition-colors">
              <User className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
