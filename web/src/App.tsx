
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from './components/ui/toaster'
import { useAuthStore } from './lib/stores/auth'
import { ConsentBanner } from './components/consent/ConsentBanner'

// Layout components
import { PublicLayout } from './components/layouts/PublicLayout'
import { AuthenticatedLayout } from './components/layouts/AuthenticatedLayout'

// Public pages
import { HomePage } from './pages/public/HomePage'
import { LoginPage } from './pages/auth/LoginPage'
import { RegisterPage } from './pages/auth/RegisterPage'

// Role-based pages
import { PetParentDashboard } from './pages/pet-parent/Dashboard'
import { VetDashboard } from './pages/vet/Dashboard'
import { HandlerDashboard } from './pages/handler/Dashboard'
import { IsolationDashboard } from './pages/isolation/Dashboard'
import { NGODashboard } from './pages/ngo/Dashboard'
import { GovernmentDashboard } from './pages/government/Dashboard'
import { AdminDashboard } from './pages/admin/Dashboard'

// Feature pages
import { PetsPage } from './pages/pets/PetsPage'
import { BookingsPage } from './pages/bookings/BookingsPage'
import { PassportPage } from './pages/passport/PassportPage'

// Auth guard component
const ProtectedRoute = ({ children, allowedRoles }: { children: React.ReactNode, allowedRoles?: string[] }) => {
  const { user, isAuthenticated } = useAuthStore()
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return <Navigate to="/unauthorized" replace />
  }
  
  return <>{children}</>
}

// Role-based dashboard router
const DashboardRouter = () => {
  const { user } = useAuthStore()
  
  if (!user) return <Navigate to="/login" replace />
  
  switch (user.role) {
    case 'pet_parent':
      return <PetParentDashboard />
    case 'vet':
      return <VetDashboard />
    case 'handler':
      return <HandlerDashboard />
    case 'isolation_center':
      return <IsolationDashboard />
    case 'ngo':
      return <NGODashboard />
    case 'government':
      return <GovernmentDashboard />
    case 'admin':
      return <AdminDashboard />
    default:
      return <Navigate to="/unauthorized" replace />
  }
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-background">
          <Routes>
            {/* Public routes */}
            <Route path="/" element={<PublicLayout />}>
              <Route index element={<HomePage />} />
              <Route path="login" element={<LoginPage />} />
              <Route path="register" element={<RegisterPage />} />
            </Route>
            
            {/* Protected routes */}
            <Route path="/app" element={
              <ProtectedRoute>
                <AuthenticatedLayout />
              </ProtectedRoute>
            }>
              <Route index element={<DashboardRouter />} />
              <Route path="dashboard" element={<DashboardRouter />} />
              
              {/* Pet management */}
              <Route path="pets" element={
                <ProtectedRoute allowedRoles={['pet_parent', 'vet']}>
                  <PetsPage />
                </ProtectedRoute>
              } />
              
              {/* Bookings */}
              <Route path="bookings" element={
                <ProtectedRoute allowedRoles={['pet_parent', 'vet', 'handler']}>
                  <BookingsPage />
                </ProtectedRoute>
              } />
              
              {/* FurrWings Passport */}
              <Route path="passport" element={
                <ProtectedRoute allowedRoles={['pet_parent', 'vet', 'handler', 'isolation_center']}>
                  <PassportPage />
                </ProtectedRoute>
              } />
            </Route>
            
            {/* Error pages */}
            <Route path="/unauthorized" element={
              <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                  <h1 className="text-2xl font-bold text-red-600">Unauthorized</h1>
                  <p className="text-gray-600">You don't have permission to access this page.</p>
                </div>
              </div>
            } />
            
            {/* Catch all - redirect to home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          
          {/* Global components */}
          <ConsentBanner />
          <Toaster />
        </div>
      </Router>
    </QueryClientProvider>
  )
}

export default App
