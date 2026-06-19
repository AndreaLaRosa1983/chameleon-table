import useAuthStore from '../store/useAuthStore'

const BASE_URL = 'http://localhost:8000'

function authHeaders() {
  const token = useAuthStore.getState().token
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

export const register = async (username, email, password) => {
  const res = await fetch(`${BASE_URL}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const login = async (username, password) => {
  const res = await fetch(`${BASE_URL}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const createRoom = async (maxPlayers) => {
  const res = await fetch(`${BASE_URL}/rooms`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ max_players: maxPlayers }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const joinRoom = async (roomCode) => {
  const res = await fetch(`${BASE_URL}/rooms/${roomCode}/join`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({}),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const startRoom = async (roomCode) => {
  const res = await fetch(`${BASE_URL}/rooms/${roomCode}/start`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({}),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const getRooms = async () => {
  const res = await fetch(`${BASE_URL}/rooms`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const getActiveRooms = async () => {
  const res = await fetch(`${BASE_URL}/rooms/active`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const observeRoom = async (roomCode) => {
  const res = await fetch(`${BASE_URL}/rooms/${roomCode}/observe`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({}),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const drawCard = async (roomCode) => {
  const res = await fetch(`${BASE_URL}/rooms/${roomCode}/draw`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({}),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const placeCard = async (roomCode, rowIndex) => {
  const res = await fetch(`${BASE_URL}/rooms/${roomCode}/place`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ row_index: rowIndex }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const takeRow = async (roomCode, rowIndex) => {
  const res = await fetch(`${BASE_URL}/rooms/${roomCode}/take-row`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ row_index: rowIndex }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const leaveRoom = async (roomCode) => {
  const res = await fetch(`${BASE_URL}/rooms/${roomCode}/leave`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({}),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}