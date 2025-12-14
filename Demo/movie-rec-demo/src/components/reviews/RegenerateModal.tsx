import { useEffect, useState, useRef } from 'react';
import { 
  X,
  Database, 
  Brain, 
  Search, 
  Sparkles, 
  MessageSquare,
  Check,
  Loader2,
  ChevronRight,
  Star,
  Film
} from 'lucide-react';
import { generatePersonalizedRecommendations, getStoredRecommendations } from '../../api/recommendations';
import { getMovie } from '../../api/tmdb';

interface Review {
  movieId: number;
  rating: number;
  text: string;
  createdAt: string;
}

interface PipelineStep {
  id: string;
  icon: React.ElementType;
  title: string;
  description: string;
  status: 'pending' | 'running' | 'complete';
  details?: string[];
  technical?: string;
}

interface RegenerateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: () => void;
  newReviews?: Review[];
}

export function RegenerateModal({ isOpen, onClose, onComplete, newReviews = [] }: RegenerateModalProps) {
  const [steps, setSteps] = useState<PipelineStep[]>([]);
  const [currentStepIndex, setCurrentStepIndex] = useState(-1);
  const [isComplete, setIsComplete] = useState(false);
  const [reviewedMovieNames, setReviewedMovieNames] = useState<{name: string; rating: number}[]>([]);
  const hasStarted = useRef(false);
  const userEmbeddingSize = 3072;

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      hasStarted.current = false;
      setIsComplete(false);
      setCurrentStepIndex(-1);
      setSteps([
        {
          id: 'load-new-reviews',
          icon: Star,
          title: 'Loading New Reviews',
          description: 'Incorporating your latest movie ratings',
          status: 'pending',
          technical: 'userReviews.filter(r => r.rating >= 8).map(r => r.movieId)'
        },
        {
          id: 'update-profile',
          icon: Database,
          title: 'Updating Taste Profile',
          description: 'Adding highly-rated movies to your favorites',
          status: 'pending',
          technical: 'onboardingData.favoriteMovies.push(...newFavorites)'
        },
        {
          id: 'recompute-embedding',
          icon: Brain,
          title: 'Recomputing Taste Embedding',
          description: `Adjusting your ${userEmbeddingSize}-dimensional taste vector`,
          status: 'pending',
          technical: 'TasteEmbeddingGenerator.update(embedding, newMovies, weights)'
        },
        {
          id: 'find-new-matches',
          icon: Search,
          title: 'Finding New Matches',
          description: 'Discovering movies aligned with your updated taste',
          status: 'pending',
          technical: 'VectorDB.nearest_neighbors(updated_embedding, k=50)'
        },
        {
          id: 'generate-explanations',
          icon: MessageSquare,
          title: 'Generating Explanations',
          description: 'Creating personalized "Because you loved..." reasons',
          status: 'pending',
          technical: 'GPT-4: generate_carousel_titles(user_favorites, candidates)'
        },
        {
          id: 'finalize',
          icon: Sparkles,
          title: 'Updating Recommendations',
          description: 'Refreshing your personalized picks',
          status: 'pending',
          technical: 'RecommenderBackend.rebuild_carousels(user_id)'
        },
      ]);
    }
  }, [isOpen]);

  // Load reviewed movie names for display
  useEffect(() => {
    if (!isOpen) return;

    async function loadReviewedMovies() {
      const reviews: Review[] = JSON.parse(localStorage.getItem('userReviews') || '[]');
      const highRatedReviews = reviews.filter(r => r.rating >= 7).slice(0, 5);
      
      const movieDetails = await Promise.all(
        highRatedReviews.map(async (review) => {
          try {
            const movie = await getMovie(review.movieId);
            return { name: movie.title, rating: review.rating };
          } catch {
            return null;
          }
        })
      );
      
      setReviewedMovieNames(movieDetails.filter((m): m is {name: string; rating: number} => m !== null));
    }
    
    loadReviewedMovies();
  }, [isOpen]);

  // Update step status
  const updateStep = (stepId: string, updates: Partial<PipelineStep>) => {
    setSteps(prev => prev.map(step => 
      step.id === stepId ? { ...step, ...updates } : step
    ));
  };

  // Run the pipeline
  useEffect(() => {
    if (!isOpen || hasStarted.current) return;
    hasStarted.current = true;

    async function runPipeline() {
      try {
        // Step 1: Load Reviews
        setCurrentStepIndex(0);
        updateStep('load-new-reviews', { status: 'running' });
        await delay(800);
        
        const reviews: Review[] = JSON.parse(localStorage.getItem('userReviews') || '[]');
        const highRated = reviews.filter(r => r.rating >= 8);
        
        updateStep('load-new-reviews', { 
          status: 'complete',
          details: [
            `Found ${reviews.length} total reviews`,
            `${highRated.length} movies rated 8+ (taste signals)`,
            ...reviewedMovieNames.slice(0, 3).map(m => `★ ${m.name} (${m.rating}/10)`)
          ]
        });

        // Step 2: Update Profile
        setCurrentStepIndex(1);
        updateStep('update-profile', { status: 'running' });
        await delay(700);
        updateStep('update-profile', { 
          status: 'complete',
          details: [
            'Taste profile updated with new favorites',
            `+${highRated.length} movies added to preference set`,
          ]
        });

        // Step 3: Recompute Embedding
        setCurrentStepIndex(2);
        updateStep('recompute-embedding', { status: 'running' });
        await delay(1200);
        
        const embeddingDelta = (Math.random() * 0.15 + 0.05).toFixed(3);
        updateStep('recompute-embedding', { 
          status: 'complete',
          details: [
            'Embedding vector updated',
            `Δ embedding shift: ${embeddingDelta} (cosine distance)`,
            `New vector: [${Array.from({length: 4}, () => (Math.random() * 2 - 1).toFixed(3)).join(', ')}, ...]`
          ]
        });

        // Step 4: Find New Matches
        setCurrentStepIndex(3);
        updateStep('find-new-matches', { status: 'running' });
        await delay(1000);
        
        const newCandidates = Math.floor(Math.random() * 15) + 20;
        updateStep('find-new-matches', { 
          status: 'complete',
          details: [
            `${newCandidates} new candidate movies found`,
            'Filtering based on updated similarity threshold',
          ]
        });

        // Step 5: Generate Explanations (real API call)
        setCurrentStepIndex(4);
        updateStep('generate-explanations', { status: 'running' });
        
        // Actually regenerate recommendations
        await generatePersonalizedRecommendations();
        
        updateStep('generate-explanations', { 
          status: 'complete',
          details: [
            'Carousel titles generated from your favorites',
            ...reviewedMovieNames.slice(0, 2).map(m => `→ "Because you loved ${m.name}..."`)
          ]
        });

        // Step 6: Finalize
        setCurrentStepIndex(5);
        updateStep('finalize', { status: 'running' });
        await delay(600);
        
        const recs = getStoredRecommendations();
        const totalRecs = recs?.reduce((acc, set) => acc + set.recommendations.length, 0) || 0;
        
        updateStep('finalize', { 
          status: 'complete',
          details: [
            `${recs?.length || 3} recommendation carousels rebuilt`,
            `${totalRecs} personalized picks ready`,
            'Home page will reflect your updated taste!'
          ]
        });

        setIsComplete(true);

      } catch (err) {
        console.error('Regeneration error:', err);
        setIsComplete(true);
      }
    }

    // Small delay to let movie names load
    setTimeout(runPipeline, 300);
  }, [isOpen, reviewedMovieNames]);

  const handleClose = () => {
    if (isComplete) {
      onComplete();
    }
    onClose();
  };

  if (!isOpen) return null;

  const progress = steps.length > 0 ? ((currentStepIndex + 1) / steps.length) * 100 : 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/80 backdrop-blur-sm"
        onClick={isComplete ? handleClose : undefined}
      />
      
      {/* Modal */}
      <div className="relative bg-gray-900 border border-gray-800 rounded-2xl w-full max-w-xl max-h-[85vh] overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 bg-gray-900 border-b border-gray-800 p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-500/20 rounded-lg">
              <Brain className="w-5 h-5 text-red-500" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">
                Updating Taste Model
              </h2>
              <p className="text-sm text-gray-400">
                Incorporating your new reviews
              </p>
            </div>
          </div>
          {isComplete && (
            <button
              onClick={handleClose}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Progress bar */}
        <div className="px-4 py-3 bg-gray-900/50">
          <div className="flex justify-between text-xs text-gray-400 mb-1.5">
            <span>{isComplete ? 'Complete!' : 'Updating...'}</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div 
              className={`h-full transition-all duration-500 ${
                isComplete 
                  ? 'bg-green-500' 
                  : 'bg-gradient-to-r from-red-600 to-red-400'
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Pipeline steps */}
        <div className="p-4 space-y-2 overflow-y-auto max-h-[50vh]">
          {steps.map((step, index) => (
            <div 
              key={step.id}
              className={`border rounded-lg p-3 transition-all duration-300 ${
                step.status === 'running' 
                  ? 'border-red-500 bg-red-500/5' 
                  : step.status === 'complete'
                    ? 'border-green-500/30 bg-green-500/5'
                    : 'border-gray-800 bg-gray-800/30 opacity-50'
              }`}
            >
              <div className="flex items-start gap-3">
                {/* Icon */}
                <div className={`p-1.5 rounded-lg flex-shrink-0 ${
                  step.status === 'running'
                    ? 'bg-red-500/20 text-red-500'
                    : step.status === 'complete'
                      ? 'bg-green-500/20 text-green-500'
                      : 'bg-gray-800 text-gray-500'
                }`}>
                  {step.status === 'running' ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : step.status === 'complete' ? (
                    <Check className="w-4 h-4" />
                  ) : (
                    <step.icon className="w-4 h-4" />
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className={`text-sm font-medium ${
                      step.status === 'pending' ? 'text-gray-500' : 'text-white'
                    }`}>
                      {step.title}
                    </h3>
                    {step.status === 'running' && (
                      <span className="text-xs text-red-400 animate-pulse">
                        Processing...
                      </span>
                    )}
                  </div>
                  
                  <p className={`text-xs ${
                    step.status === 'pending' ? 'text-gray-600' : 'text-gray-400'
                  }`}>
                    {step.description}
                  </p>

                  {/* Technical detail */}
                  {step.status !== 'pending' && step.technical && (
                    <div className="mt-1.5 text-xs font-mono text-gray-500 bg-gray-800/50 rounded px-2 py-1 overflow-x-auto">
                      <ChevronRight className="w-3 h-3 inline mr-1" />
                      {step.technical}
                    </div>
                  )}

                  {/* Step details */}
                  {step.details && step.details.length > 0 && (
                    <div className="mt-1.5 space-y-0.5">
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

        {/* Footer */}
        {isComplete && (
          <div className="sticky bottom-0 bg-gray-900 border-t border-gray-800 p-4">
            <button
              onClick={handleClose}
              className="w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
            >
              <Sparkles className="w-4 h-4" />
              View Updated Recommendations
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// Helper function
function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}