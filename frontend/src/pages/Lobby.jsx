import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import useGameStore from '../store/useGameStore'
import { createRoom, joinRoom, getRooms } from '../api/api'
import s from './Lobby.module.scss'

function Lobby() {
  const navigate = useNavigate()
  const { playerName, setPlayerName, setRoomCode } = useGameStore()

  const [maxPlayers, setMaxPlayers] = useState(3)
  const [rooms, setRooms] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchRooms = async () => {
      try {
        const data = await getRooms()
        setRooms(data.rooms)
      } catch (e) {
        console.error(e)
      }
    }
    fetchRooms()
    const interval = setInterval(fetchRooms, 3000)
    return () => clearInterval(interval)
  }, [])

  const handleCreate = async () => {
    if (!playerName) return setError('Please enter your name')
    try {
      const data = await createRoom(playerName, maxPlayers)
      setRoomCode(data.room_code)
      navigate(`/waiting/${data.room_code}`)
    } catch (e) {
      setError('Error creating room')
    }
  }

  const handleJoin = async (roomCode) => {
    if (!playerName) return setError('Please enter your name before joining')
    try {
      await joinRoom(roomCode, playerName)
      setRoomCode(roomCode)
      navigate(`/waiting/${roomCode}`)
    } catch (e) {
      setError('Error joining room')
    }
  }

  return (
    <div className={s.page}>

      <div className={s.logo}>
        <div className={s.logoTitle}>🦎 Chameleon Table</div>
        <div className={s.logoSub}>online card game</div>
      </div>

      {error && <div className={s.error}>{error}</div>}

      <div className={s.card}>
        <div className={s.cardTitle}>Create a room</div>
        <div className={s.formRow}>
          <input
            className={s.input}
            placeholder="Your name"
            value={playerName || ''}
            onChange={(e) => { setPlayerName(e.target.value); setError(null) }}
          />
          <select
            className={s.select}
            value={maxPlayers}
            onChange={(e) => setMaxPlayers(Number(e.target.value))}
          >
            <option value={2}>2 players</option>
            <option value={3}>3 players</option>
            <option value={4}>4 players</option>
            <option value={5}>5 players</option>
          </select>
          <button className={s.btnPrimary} onClick={handleCreate}>Create</button>
        </div>
      </div>

      <div className={s.sectionTitle}>Available rooms</div>

      <div className={s.roomList}>
        {rooms.length === 0 && <div className={s.empty}>No rooms available</div>}
        {rooms.map((room) => (
          <div key={room.room_code} className={s.roomItem}>
            <div>
              <div className={s.roomCode}>{room.room_code}</div>
              <div className={s.roomMeta}>{room.players} / {room.max_players} players · waiting</div>
            </div>
            <button className={s.btnJoin} onClick={() => handleJoin(room.room_code)}>
              Join →
            </button>
          </div>
        ))}
      </div>

    </div>
  )
}

export default Lobby
