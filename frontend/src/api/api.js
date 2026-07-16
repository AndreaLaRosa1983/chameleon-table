import useAuthStore from '../store/useAuthStore'

const BASE_URL = '/api'

function authHeaders() {
  const token = useAuthStore.getState().token
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

/**
 * Centralized fetch wrapper: on 401 (expired or invalidated token) clears auth
 * state and redirects to login, instead of failing silently or leaving a broken
 * game on screen.
 */
async function apiFetch(url, options = {}) {
  const res = await fetch(url, options)

  if (res.status === 401) {
    useAuthStore.getState().clearAuth()
    // Full reload rather than router navigation: guarantees no stale in-memory
    // state survives an expired session. 
    window.location.href = '/login'
    throw new Error('Session expired, please log in again')
  }

  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const register = async (username, email, password) => {
  return apiFetch(`${BASE_URL}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password }),
  })
}

export const login = async (username, password) => {
  return apiFetch(`${BASE_URL}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
}

export const createRoom = async (maxPlayers) => {
  return apiFetch(`${BASE_URL}/rooms`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ max_players: maxPlayers }),
  })
}

export const joinRoom = async (roomCode) => {
  return apiFetch(`${BASE_URL}/rooms/${roomCode}/join`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({}),
  })
}

export const startRoom = async (roomCode) => {
  return apiFetch(`${BASE_URL}/rooms/${roomCode}/start`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({}),
  })
}

export const getRooms = async () => {
  return apiFetch(`${BASE_URL}/rooms`)
}

export const getActiveRooms = async () => {
  return apiFetch(`${BASE_URL}/rooms/active`)
}

export const observeRoom = async (roomCode) => {
  return apiFetch(`${BASE_URL}/rooms/${roomCode}/observe`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({}),
  })
}

export const drawCard = async (roomCode) => {
  return apiFetch(`${BASE_URL}/rooms/${roomCode}/draw`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({}),
  })
}

export const placeCard = async (roomCode, rowIndex) => {
  return apiFetch(`${BASE_URL}/rooms/${roomCode}/place`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ row_index: rowIndex }),
  })
}

export const takeRow = async (roomCode, rowIndex) => {
  return apiFetch(`${BASE_URL}/rooms/${roomCode}/take-row`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ row_index: rowIndex }),
  })
}

export const leaveRoom = async (roomCode) => {
  return apiFetch(`${BASE_URL}/rooms/${roomCode}/leave`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({}),
  })
}

export const getScores = async (roomCode) => {
  return apiFetch(`${BASE_URL}/rooms/${roomCode}/scores`, {
    headers: authHeaders(),
  })
}

export const abortGame = async (roomCode) => {
  return apiFetch(`${BASE_URL}/rooms/${roomCode}/abort`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({}),
  })
}

export const leaveObserve = async (roomCode) => {
  return apiFetch(`${BASE_URL}/rooms/${roomCode}/leave-observe`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({}),
  })
}