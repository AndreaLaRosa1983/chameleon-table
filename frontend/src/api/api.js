const BASE_URL = 'http://localhost:8000'

export const createRoom = async (playerName, maxPlayers) => {
  const res = await fetch(`${BASE_URL}/rooms`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ player_name: playerName, max_players: maxPlayers }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const joinRoom = async (roomCode, playerName) => {
  const res = await fetch(`${BASE_URL}/rooms/${roomCode}/join`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ player_name: playerName }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const startRoom = async (roomCode, playerName) => {
  const res = await fetch(`${BASE_URL}/rooms/${roomCode}/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ player_name: playerName }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const getRooms = async () => {
  const res = await fetch(`${BASE_URL}/rooms`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const drawCard = async (roomCode, playerName) => {
  const res = await fetch(`${BASE_URL}/rooms/${roomCode}/draw`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ player_name: playerName }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const placeCard = async (roomCode, playerName, rowIndex) => {
  const res = await fetch(`${BASE_URL}/rooms/${roomCode}/place`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ player_name: playerName, row_index: rowIndex }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const takeRow = async (roomCode, playerName, rowIndex) => {
  const res = await fetch(`${BASE_URL}/rooms/${roomCode}/take-row`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ player_name: playerName, row_index: rowIndex }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const leaveRoom = async (roomCode, playerName) => {
  const res = await fetch(`${BASE_URL}/rooms/${roomCode}/leave`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ player_name: playerName }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}