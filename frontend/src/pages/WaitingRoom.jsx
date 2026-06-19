import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import useGameStore from '../store/useGameStore'
import useAuthStore from '../store/useAuthStore'
import useGameSocket from '../hooks/useGameSocket'
import { startRoom } from '../api/api'
import s from './WaitingRoom.module.scss'

function WaitingRoom() {
  const { roomCode } = useParams()
  const navigate = useNavigate()
  const { gameState } = useGameStore()
  const { username } = useAuthStore()

  useGameSocket(roomCode)

  useEffect(() => {
    if (gameState?.phase === 'playing') {
      navigate(`/game/${roomCode}`)
    }
  }, [gameState?.phase])

  const handleStart = async () => {
    try {
      await startRoom(roomCode)
    } catch (e) {
      console.error('Error starting room:', e)
    }
  }

  const players = gameState?.turn_order ?? []
  const canStart = players.length >= 2
  const isHost = players[0] === username

  return (
    <div className={s.page}>

      <div className={s.logoTitle}>🦎 Chameleon Table</div>

      <div className={s.roomHeader}>
        <div className={s.roomTitle}>Waiting Room</div>
        <div className={s.roomCodeRow}>
          <span className={s.roomCodeLabel}>room code</span>
          <span className={s.roomCode}>{roomCode}</span>
        </div>
      </div>

      <div className={s.card}>
        <div className={s.cardTitle}>Players ({players.length})</div>
        <div className={s.playerList}>
          {players.map((name, i) => (
            <div key={name} className={s.playerItem}>
              <div className={`${s.playerDot} ${i === 0 ? s.playerDotHost : ''}`} />
              <span className={s.playerName}>{name}</span>
              {i === 0 && <span className={s.hostBadge}>host</span>}
            </div>
          ))}
        </div>
      </div>

      <div className={s.actions}>
        {isHost && (
          <>
            <button
              className={s.btnStart}
              onClick={handleStart}
              disabled={!canStart}
            >
              Start game
            </button>
            {!canStart && (
              <span className={s.hint}>At least 2 players needed to start</span>
            )}
          </>
        )}
        {!isHost && (
          <div className={s.waiting}>
            <div className={s.dot} />
            <div className={s.dot} />
            <div className={s.dot} />
            Waiting for the host to start…
          </div>
        )}
      </div>

    </div>
  )
}

export default WaitingRoom