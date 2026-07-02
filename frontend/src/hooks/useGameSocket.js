import { useEffect, useRef } from 'react'
import useGameStore from '../store/useGameStore'
import useAuthStore from '../store/useAuthStore'

const WS_URL = import.meta.env.VITE_WS_URL || `ws://${window.location.host}`

const useGameSocket = (roomCode) => {
  const setGameState = useGameStore((state) => state.setGameState)
  const token = useAuthStore((state) => state.token)
  const wsRef = useRef(null)
  const lastSeqRef = useRef(-1)

  useEffect(() => {
    if (!roomCode || !token) return

    lastSeqRef.current = -1

    const timer = setTimeout(() => {
      const ws = new WebSocket(`${WS_URL}/ws/${roomCode}?token=${encodeURIComponent(token)}`)
      wsRef.current = ws

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.sequence_number < lastSeqRef.current) {
          console.log('WS ignored stale message:', data.sequence_number)
          return
        }
        lastSeqRef.current = data.sequence_number
        console.log('WS received:', data.current_turn, data.phase)
        setGameState(data)
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      ws.onclose = () => {
        console.log('WebSocket closed')
      }
    }, 100)

    return () => {
      clearTimeout(timer)
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [roomCode, token])

  return wsRef
}

export default useGameSocket