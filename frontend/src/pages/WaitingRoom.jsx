import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import useGameStore from '../store/useGameStore'
import useGameSocket from '../hooks/useGameSocket'
import { startRoom } from '../api/api'

function WaitingRoom() {
  const { roomCode } = useParams()
  const navigate = useNavigate()
  const { playerName, gameState } = useGameStore()

  useGameSocket(roomCode, playerName)

  // when the game starts, navigate to the game page
  useEffect(() => {
    if (gameState?.phase === 'playing') {
      navigate(`/game/${roomCode}`)
    }
  }, [gameState?.phase])

  const handleStart = async () => {
    try {
      await startRoom(roomCode, playerName)
    } catch (e) {
      console.error('Error starting room:', e)
    }
  }

  const players = gameState?.turn_order ?? []
  const canStart = players.length >= 2
  const isHost = players[0] === playerName

  return (
    <div>
      <h1>Waiting Room</h1>
      <p>Room code: <strong>{roomCode}</strong></p>

      <h2>Players ({players.length})</h2>
      <ul>
        {players.map((name) => (
          <li key={name}>{name}</li>
        ))}
      </ul>

      {isHost && (
        <button onClick={handleStart} disabled={!canStart}>
          Start game
        </button>
      )}
      {isHost && !canStart && <p>At least 2 players needed to start</p>}
      {!isHost && <p>Waiting for the host to start the game...</p>}
    </div>
  )
}

export default WaitingRoom