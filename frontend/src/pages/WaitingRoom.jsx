import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import useGameStore from '../store/useGameStore'
import useAuthStore from '../store/useAuthStore'
import useGameSocket from '../hooks/useGameSocket'
import { startRoom, abortGame } from '../api/api'
import s from './WaitingRoom.module.scss'

function WaitingRoom() {
  const { roomCode } = useParams()
  const navigate = useNavigate()
  const { gameState, clearSession } = useGameStore()
  const { username } = useAuthStore()
  const [showAbort, setShowAbort] = useState(false)

  useGameSocket(roomCode)

  useEffect(() => {
    if (gameState?.phase === 'playing') {
      navigate(`/game/${roomCode}`)
    }
    if (gameState?.phase === 'aborted') {
      clearSession()
      navigate('/')
    }
  }, [gameState?.phase])

  const handleStart = async () => {
    try {
      await startRoom(roomCode)
    } catch (e) {
      console.error('Error starting room:', e)
    }
  }

  const handleAbortConfirm = async () => {
    try {
      await abortGame(roomCode)
      clearSession()
      navigate('/')
    } catch (e) {
      console.error('Error aborting room:', e)
    }
    setShowAbort(false)
  }

  const players = gameState?.turn_order ?? []
  const canStart = players.length >= 2
  const isHost = players[0] === username

  return (
    <div className={s.page}>

      {showAbort && (
        <div className={s.modalOverlay}>
          <div className={s.modalBox}>
            <span className={s.modalTitle}>Cancel the room?</span>
            <span className={s.modalSubtitle}>All players will be returned to the lobby.</span>
            <div className={s.modalButtons}>
              <button onClick={handleAbortConfirm} className={s.btnDanger}>Cancel room</button>
              <button onClick={() => setShowAbort(false)} className={s.btnConfirm}>Stay</button>
            </div>
          </div>
        </div>
      )}

      <div className={s.logoTitle}>
          <img src="/assets/chameleon-logo.svg" alt="" className={s.logoIcon} />
        Chameleon Table
      </div>

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
            <button className={s.btnAbort} onClick={() => setShowAbort(true)}>
              Cancel room
            </button>
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