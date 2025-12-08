import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { PageLayout } from './components/layout/PageLayout';
import { HomePage } from './pages/HomePage';
import { AuthPage } from './pages/AuthPage';
import { TMDBCallbackPage } from './pages/TMDBCallbackPage';
import { PersonalizingPage } from './pages/PersonalizingPage';
import { ReviewsPage } from './pages/ReviewsPage';
import { VisualizationPage } from './pages/VisualizationPage';
import { ProfilePage } from './pages/ProfilePage';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/auth" element={<AuthPage />} />
          <Route path="/auth/tmdb/callback" element={<TMDBCallbackPage />} />
          <Route path="/personalizing" element={<PersonalizingPage />} />

          {/* Protected routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <PageLayout>
                  <HomePage />
                </PageLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/reviews"
            element={
              <ProtectedRoute>
                <PageLayout>
                  <ReviewsPage />
                </PageLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/visualization"
            element={
              <ProtectedRoute>
                <PageLayout>
                  <VisualizationPage />
                </PageLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <PageLayout>
                  <ProfilePage />
                </PageLayout>
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;