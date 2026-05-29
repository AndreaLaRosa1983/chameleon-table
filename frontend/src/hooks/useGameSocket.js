import { useEffect, useRef } from 'react'
import useGameStore from '../store/useGameStore'

const WS_URL = import.meta.env.VITE_WS_URL

const useGameSocket = (roomCode, playerName) => {
  const setGameState = useGameStore((state) => state.setGameState)
  const wsRef = useRef(null)

  useEffect(() => {
    if (!roomCode || !playerName) return

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
    }

    return () => {
      ws.close()
    }
  }, [roomCode, playerName, setGameState])

  return wsRef
}

export default useGameSocket