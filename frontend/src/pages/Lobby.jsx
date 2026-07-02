import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import useGameStore from '../store/useGameStore'
import useAuthStore from '../store/useAuthStore'
import { createRoom, joinRoom, getRooms, getActiveRooms, observeRoom } from '../api/api'
import s from './Lobby.module.scss'

function Lobby() {
  const navigate = useNavigate()
  const { setRoomCode } = useGameStore()
  const { username, clearAuth } = useAuthStore()

  const [maxPlayers, setMaxPlayers] = useState(3)
  const [rooms, setRooms] = useState([])
  const [activeRooms, setActiveRooms] = useState([])
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
    const fetchActiveRooms = async () => {
      try {
        const data = await getActiveRooms()
        setActiveRooms(data.rooms)
      } catch (e) {
        console.error(e)
      }
    }
    fetchRooms()
    fetchActiveRooms()
    const interval = setInterval(() => {
      fetchRooms()
      fetchActiveRooms()
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  const handleCreate = async () => {
    try {
      const data = await createRoom(maxPlayers)
      setRoomCode(data.room_code)
      navigate(`/waiting/${data.room_code}`)
    } catch (e) {
      setError('Error creating room')
    }
  }

  const handleJoin = async (roomCode, alreadyInRoom) => {
    if (alreadyInRoom) {
      setRoomCode(roomCode)
      navigate(`/waiting/${roomCode}`)
      return
    }
    try {
      await joinRoom(roomCode)
      setRoomCode(roomCode)
      navigate(`/waiting/${roomCode}`)
    } catch (e) {
      setError('Error joining room')
    }
  }

  const handleObserve = async (roomCode) => {
    try {
      await observeRoom(roomCode)
      setRoomCode(roomCode)
      navigate(`/observe/${roomCode}`)
    } catch (e) {
      setError('Error joining as observer')
    }
  }

  const handleLogout = () => {
    clearAuth()
    navigate('/login')
  }

  return (
    <div className={s.page}>

      <div className={s.logo}>
        <div className={s.logoTitle}>🦎 Chameleon Table</div>
        <div className={s.logoSub}>online card game</div>
      </div>

      <div className={s.userBar}>
        Logged in as <strong>{username}</strong>
        <button className={s.btnLogout} onClick={handleLogout}>Logout</button>
      </div>

      {error && <div className={s.error}>{error}</div>}

      <div className={s.card}>
        <div className={s.cardTitle}>Create a room</div>
        <div className={s.formRow}>
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
        {rooms.map((room) => {
          const alreadyInRoom = room.players_list?.includes(username)
          return (
            <div key={room.room_code} className={`${s.roomItem} ${alreadyInRoom ? s.myRoom : ''}`}>
              <div>
                <div className={s.roomCode}>
                  {room.room_code}
                  {alreadyInRoom && <span className={s.myBadge}>YOU'RE IN</span>}
                </div>
                <div className={s.roomMeta}>{room.players} / {room.max_players} players · waiting</div>
              </div>
              <button
                className={alreadyInRoom ? s.btnRejoin : s.btnJoin}
                onClick={() => handleJoin(room.room_code, alreadyInRoom)}
              >
                {alreadyInRoom ? 'Rejoin →' : 'Join →'}
              </button>
            </div>
          )
        })}
      </div>

      <div className={s.sectionTitle}>Live games</div>

      <div className={s.roomList}>
        {activeRooms.length === 0 && <div className={s.empty}>No live games</div>}
        {activeRooms.map((room) => {
          const alreadyInRoom = room.players_list?.includes(username)
          return (
            <div key={room.room_code} className={`${s.roomItem} ${s.liveItem}`}>
              <div>
                <div className={s.roomCode}>
                  {room.room_code} <span className={s.liveBadge}>LIVE</span>
                  {alreadyInRoom && <span className={s.myBadge}>YOU'RE IN</span>}
                </div>
                <div className={s.roomMeta}>{room.players} / {room.max_players} players · in progress</div>
              </div>
              {alreadyInRoom
                ? <button className={s.btnRejoin} onClick={() => { setRoomCode(room.room_code); navigate(`/game/${room.room_code}`) }}>
                    Rejoin →
                  </button>
                : <button className={s.btnWatch} onClick={() => handleObserve(room.room_code)}>
                    👁 Watch
                  </button>
              }
            </div>
          )
        })}
      </div>

    </div>
  )
}

export default Lobby
