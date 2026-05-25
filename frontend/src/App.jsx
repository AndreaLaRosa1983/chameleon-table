import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Lobby from './pages/Lobby'
import WaitingRoom from './pages/WaitingRoom'
import Game from './pages/Game'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Lobby />} />
        <Route path="/waiting/:roomCode" element={<WaitingRoom />} />
        <Route path="/game/:roomCode" element={<Game />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App