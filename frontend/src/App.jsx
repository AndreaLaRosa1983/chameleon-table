import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Lobby from './pages/Lobby'
import WaitingRoom from './pages/WaitingRoom'
import Game from './pages/Game'
import Results from './pages/Results_old'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Lobby />} />
        <Route path="/waiting/:roomCode" element={<WaitingRoom />} />
        <Route path="/game/:roomCode" element={<Game />} />
        <Route path="/results/:roomCode" element={<Results />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App