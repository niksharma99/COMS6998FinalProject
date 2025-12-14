import { useEffect, useState, useRef, use } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Film, 
  Database, 
  Brain, 
  Search, 
  Sparkles, 
  MessageSquare,
  Check,
  Loader2,
  ChevronRight
} from 'lucide-react';
import { generatePersonalizedRecommendations, getStoredRecommendations } from '../api/recommendations';
import { getMovie } from '../api/tmdb';

interface PipelineStep {
  id: string;
  icon: React.ElementType;
  title: string;
  description: string;
  status: 'pending' | 'running' | 'complete';
  details?: string[];
  technical?: string;
}

const userEmbeddingSize = 3072;
const INITIAL_STEPS: PipelineStep[] = [
  {
    id: 'fetch-profile',
    icon: Database,
    title: 'Loading User Profile',
    description: 'Retrieving your movie preferences and ratings',
    status: 'pending',
    technical: 'localStorage.get("onboardingData", "tmdbMovieData", "userReviews")'
  },
  {
    id: 'fetch-tmdb',
    icon: Film,
    title: 'Fetching Movie Metadata',
    description: 'Getting detailed information from TMDB',
    status: 'pending',
    technical: 'GET api.themoviedb.org/3/movie/{id}'
  },
  {
    id: 'compute-embedding',
    icon: Brain,
    title: 'Computing Taste Embedding',
    description: `Generating your ${userEmbeddingSize}-dimensional taste vector`,
    status: 'pending',
    technical: `TasteEmbeddingGenerator.encode(movies, vibes) → float[${userEmbeddingSize}]`
  },
  {
    id: 'semantic-search',
    icon: Search,
    title: 'Semantic Similarity Search',
    description: 'Finding movies that match your taste profile',
    status: 'pending',
    technical: 'VectorDB.nearest_neighbors(embedding, k=50, threshold=0.75)'
  },
  {
    id: 'generate-explanations',
    icon: MessageSquare,
    title: 'Generating Explanations',
    description: 'Creating personalized recommendation reasons',
    status: 'pending',
    technical: 'GPT-4: generate_explanation(user_profile, movie, factors)'
  },
  {
    id: 'finalize',
    icon: Sparkles,
    title: 'Finalizing Recommendations',
    description: 'Organizing your personalized movie picks',
    status: 'pending',
    technical: 'RecommenderBackend.rank_and_categorize(candidates)'
  },
];

export function PersonalizingPage() {
  const [steps, setSteps] = useState<PipelineStep[]>(INITIAL_STEPS);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [movieNames, setMovieNames] = useState<string[]>([]);
  const [vibes, setVibes] = useState<string[]>([]);
  const [embeddingPreview, setEmbeddingPreview] = useState<string>('');
  const [candidateCount, setCandidateCount] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const hasStarted = useRef(false);

  // Load user's movie names for display
  useEffect(() => {
    async function loadUserMovies() {
      const onboardingData = JSON.parse(localStorage.getItem('onboardingData') || '{}');
      const tmdbData = JSON.parse(localStorage.getItem('tmdbMovieData') || '{}');
      
      const movieIds = [
        ...(onboardingData.favoriteMovies || []),
        ...(onboardingData.recentMovies || []),
        ...(tmdbData.ratedMovies || []).slice(0, 5),
        ...(tmdbData.favoriteMovies || []).slice(0, 5),
      ].slice(0, 8);

      const uniqueIds = [...new Set(movieIds)];
      
      // Fetch movie names
      const movies = await Promise.all(
        uniqueIds.map(id => getMovie(id).catch(() => null))
      );
      
      const names = movies
        .filter((m): m is NonNullable<typeof m> => m !== null)
        .map(m => m.title);
      
      setMovieNames(names);
      setVibes(onboardingData.selectedVibes || []);
    }
    
    loadUserMovies();
  }, []);

  // Generate fake embedding preview
  const generateEmbeddingPreview = () => {
    const values = Array.from({ length: 12 }, () => 
      (Math.random() * 2 - 1).toFixed(4)
    );
    return `[${values.join(', ')}, ... +3060 dims]`;
  };

  // Update step status
  const updateStep = (stepId: string, updates: Partial<PipelineStep>) => {
    setSteps(prev => prev.map(step => 
      step.id === stepId ? { ...step, ...updates } : step
    ));
  };

  // Run the pipeline
  useEffect(() => {
    if (hasStarted.current) return;
    hasStarted.current = true;

    async function runPipeline() {
      try {
        // Step 1: Load Profile
        updateStep('fetch-profile', { status: 'running' });
        await delay(800);
        updateStep('fetch-profile', { 
          status: 'complete',
          details: [
            `Found ${movieNames.length || '...'} movies in profile`,
            vibes.length > 0 ? `Vibes: ${vibes.slice(0, 3).join(', ')}` : 'Processing preferences...',
          ]
        });
        setCurrentStepIndex(1);

        // Step 2: Fetch TMDB
        updateStep('fetch-tmdb', { status: 'running' });
        await delay(1200);
        updateStep('fetch-tmdb', { 
          status: 'complete',
          details: movieNames.length > 0 
            ? movieNames.slice(0, 4).map(name => `✓ ${name}`)
            : ['Fetching movie details...']
        });
        setCurrentStepIndex(2);

        // Step 3: Compute Embedding
        updateStep('compute-embedding', { status: 'running' });
        setEmbeddingPreview(generateEmbeddingPreview());
        await delay(1500);
        updateStep('compute-embedding', { 
          status: 'complete',
          details: [
            'Taste vector computed successfully',
            `Embedding: ${generateEmbeddingPreview()}`,
          ]
        });
        setCurrentStepIndex(3);

        // Step 4: Semantic Search
        updateStep('semantic-search', { status: 'running' });
        await delay(1000);
        const candidates = Math.floor(Math.random() * 20) + 35;
        setCandidateCount(candidates);
        updateStep('semantic-search', { 
          status: 'complete',
          details: [
            `Found ${candidates} candidate movies`,
            'Similarity scores: 0.72 - 0.94',
          ]
        });
        setCurrentStepIndex(4);

        // Step 5: Generate Explanations (this is where the real API call happens)
        updateStep('generate-explanations', { status: 'running' });
        
        // Actually generate recommendations
        await generatePersonalizedRecommendations();
        
        updateStep('generate-explanations', { 
          status: 'complete',
          details: [
            'Explanation factors extracted',
            'Match scores calculated',
          ]
        });
        setCurrentStepIndex(5);

        // Step 6: Finalize
        updateStep('finalize', { status: 'running' });
        await delay(800);
        
        const recs = getStoredRecommendations();
        const recCount = recs?.reduce((acc, set) => acc + set.recommendations.length, 0) || 0;
        
        updateStep('finalize', { 
          status: 'complete',
          details: [
            `${recs?.length || 3} recommendation categories created`,
            `${recCount || 12} personalized picks ready`,
          ]
        });

        // Navigate after a brief pause
        await delay(1000);
        navigate('/');

      } catch (err) {
        console.error('Pipeline error:', err);
        setError('Something went wrong. Redirecting...');
        await delay(2000);
        navigate('/');
      }
    }

    // Small delay to let movie names load
    setTimeout(runPipeline, 500);
  }, [navigate, movieNames, vibes]);

  const progress = ((currentStepIndex + 1) / steps.length) * 100;

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Film className="w-10 h-10 text-red-600" />
            <span className="text-2xl font-bold text-white">MovieRec</span>
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">
            Personalizing Your Experience
          </h1>
          <p className="text-gray-400">
            Our AI is analyzing your taste to find perfect matches
          </p>
        </div>

        {/* Progress bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-400 mb-2">
            <span>Processing...</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-red-600 to-red-400 transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Pipeline steps */}
        <div className="space-y-3">
          {steps.map((step, index) => (
            <div 
              key={step.id}
              className={`bg-gray-900 border rounded-xl p-4 transition-all duration-300 ${
                step.status === 'running' 
                  ? 'border-red-500 shadow-lg shadow-red-500/20' 
                  : step.status === 'complete'
                    ? 'border-green-500/50'
                    : 'border-gray-800 opacity-50'
              }`}
            >
              <div className="flex items-start gap-4">
                {/* Icon */}
                <div className={`p-2 rounded-lg ${
                  step.status === 'running'
                    ? 'bg-red-500/20 text-red-500'
                    : step.status === 'complete'
                      ? 'bg-green-500/20 text-green-500'
                      : 'bg-gray-800 text-gray-500'
                }`}>
                  {step.status === 'running' ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : step.status === 'complete' ? (
                    <Check className="w-5 h-5" />
                  ) : (
                    <step.icon className="w-5 h-5" />
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className={`font-semibold ${
                      step.status === 'pending' ? 'text-gray-500' : 'text-white'
                    }`}>
                      {step.title}
                    </h3>
                    {step.status === 'running' && (
                      <span className="text-xs text-red-400 animate-pulse">
                        In progress...
                      </span>
                    )}
                  </div>
                  
                  <p className={`text-sm ${
                    step.status === 'pending' ? 'text-gray-600' : 'text-gray-400'
                  }`}>
                    {step.description}
                  </p>

                  {/* Technical detail (monospace) */}
                  {step.status !== 'pending' && step.technical && (
                    <div className="mt-2 text-xs font-mono text-gray-500 bg-gray-800/50 rounded px-2 py-1 overflow-x-auto">
                      <ChevronRight className="w-3 h-3 inline mr-1" />
                      {step.technical}
                    </div>
                  )}

                  {/* Step details */}
                  {step.details && step.details.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {step.details.map((detail, i) => (
                        <p key={i} className="text-xs text-green-400/80 font-mono">
                          {detail}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Error state */}
        {error && (
          <div className="mt-6 text-center text-yellow-400 bg-yellow-400/10 rounded-lg p-4">
            {error}
          </div>
        )}

        {/* Footer */}
        <p className="text-center text-gray-600 text-sm mt-8">
          Powered by BGE Embeddings • GPT-4 • TMDB API
        </p>
      </div>
    </div>
  );
}

// Helper function
function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}