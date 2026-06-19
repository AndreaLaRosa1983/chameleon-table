import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import useAuthStore from './store/useAuthStore'
import Auth from './pages/Auth'
import Lobby from './pages/Lobby'
import WaitingRoom from './pages/WaitingRoom'
import Game from './pages/Game'
import Results from './pages/Results'
import Observer from './pages/Observer'

function ProtectedRoute({ children }) {
  const token = useAuthStore((state) => state.token)
  if (!token) return <Navigate to="/login" replace />
  return children
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Auth />} />
        <Route path="/" element={<ProtectedRoute><Lobby /></ProtectedRoute>} />
        <Route path="/waiting/:roomCode" element={<ProtectedRoute><WaitingRoom /></ProtectedRoute>} />
        <Route path="/game/:roomCode" element={<ProtectedRoute><Game /></ProtectedRoute>} />
        <Route path="/results/:roomCode" element={<ProtectedRoute><Results /></ProtectedRoute>} />
        <Route path="/observe/:roomCode" element={<ProtectedRoute><Observer /></ProtectedRoute>} />
      </Routes>
    </BrowserRouter>
  )
}

export default App