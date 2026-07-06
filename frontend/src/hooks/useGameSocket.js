import { useEffect, useRef, useState } from 'react'
import useGameStore from '../store/useGameStore'
import useAuthStore from '../store/useAuthStore'

const WS_URL = import.meta.env.VITE_WS_URL || `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`

// Websocket problem, if happen a bad connection the socket close so i need to make a pool request 
// to reconnect 
const RECONNECT_DELAYS = [1000, 2000, 3000, 5000, 8000, 10000]

const useGameSocket = (roomCode) => {
  const setGameState = useGameStore((state) => state.setGameState)
  const token = useAuthStore((state) => state.token)
  const wsRef = useRef(null)
  const lastSeqRef = useRef(-1)
  const reconnectAttemptRef = useRef(0)
  const reconnectTimerRef = useRef(null)
  const shouldReconnectRef = useRef(true)

  // 'connecting' | 'connected' | 'reconnecting' | 'disconnected'
  const [connectionStatus, setConnectionStatus] = useState('connecting')

  useEffect(() => {
    if (!roomCode || !token) return

    shouldReconnectRef.current = true
    lastSeqRef.current = -1
    reconnectAttemptRef.current = 0

    function connect() {
      setConnectionStatus(reconnectAttemptRef.current === 0 ? 'connecting' : 'reconnecting')

      const ws = new WebSocket(`${WS_URL}/ws/${roomCode}?token=${encodeURIComponent(token)}`)
      wsRef.current = ws

      ws.onopen = () => {
        reconnectAttemptRef.current = 0
        setConnectionStatus('connected')
      }

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
        if (!shouldReconnectRef.current) return

        setConnectionStatus('reconnecting')
        const delayIndex = Math.min(reconnectAttemptRef.current, RECONNECT_DELAYS.length - 1)
        const delay = RECONNECT_DELAYS[delayIndex]
        reconnectAttemptRef.current += 1

        reconnectTimerRef.current = setTimeout(() => {
          if (shouldReconnectRef.current) connect()
        }, delay)
      }
    }

    // Small initial delay, same as before, to avoid connecting before the
    // room is guarateed to exist right after creation/join.
    const initialTimer = setTimeout(connect, 100)

    return () => {
      shouldReconnectRef.current = false
      clearTimeout(initialTimer)
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current)
      if (wsRef.current) wsRef.current.close()
      setConnectionStatus('disconnected')
    }
  }, [roomCode, token])

  return { wsRef, connectionStatus }
}

export default useGameSocket