import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import useGameStore from '../store/useGameStore'
import { createRoom, joinRoom, getRooms } from '../api/api'

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
    <div>
      <h1>Chameleon Table</h1>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      <div>
        <h2>Create a room</h2>
        <input
          placeholder="Your name"
          value={playerName || ''}
          onChange={(e) => setPlayerName(e.target.value)}
        />
        <select value={maxPlayers} onChange={(e) => setMaxPlayers(Number(e.target.value))}>
          <option value={2}>2 players</option>
          <option value={3}>3 players</option>
          <option value={4}>4 players</option>
          <option value={5}>5 players</option>
        </select>
        <button onClick={handleCreate}>Create room</button>
      </div>

      <div>
        <h2>Available rooms</h2>
        {rooms.length === 0 && <p>No rooms available</p>}
        {rooms.map((room) => (
          <div key={room.room_code}>
            <span>{room.room_code} — {room.players}/{room.max_players} players</span>
            <button onClick={() => handleJoin(room.room_code)}>Join</button>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Lobby