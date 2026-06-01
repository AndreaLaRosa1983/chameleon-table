import { useEffect, useRef } from 'react'
import useGameStore from '../store/useGameStore'

const WS_URL = import.meta.env.VITE_WS_URL

const useGameSocket = (roomCode, playerName) => {
  const setGameState = useGameStore((state) => state.setGameState)
  const wsRef = useRef(null)
  const isConnected = useRef(false)

  useEffect(() => {
    if (!roomCode || !playerName) return
    if (isConnected.current) return  // evita doppia connessione in StrictMode

    isConnected.current = true

    const ws = new WebSocket(`${WS_URL}/ws/${roomCode}/${encodeURIComponent(playerName)}`)
    wsRef.current = ws

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setGameState(data)
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    ws.onclose = () => {
      console.log('WebSocket closed')
      isConnected.current = false
    }

    return () => {
      ws.close()
      isConnected.current = false
    }
  }, [roomCode, playerName])

  return wsRef
}

export default useGameSocket