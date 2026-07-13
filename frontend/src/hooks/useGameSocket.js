import { useEffect, useRef, useState } from 'react'
import useGameStore from '../store/useGameStore'
import useAuthStore from '../store/useAuthStore'

const WS_URL = import.meta.env.VITE_WS_URL || `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`
const API_URL = import.meta.env.VITE_API_URL

// Websocket problem, if happen a bad connection the socket close so i need to make a pool request to reconect 
const RECONNECT_DELAYS = [1000, 2000, 3000, 5000, 8000, 10000]

// Ping/pong tuning: more aggressive than the generic 25-30s industry standard, because the game's turn inactivity timeout is only 60s — we
// need to detect a zombie conection well before a player risks being marked inactive for a network problem that isn't their fault.
const PING_INTERVAL_MS = 20000
const PONG_TIMEOUT_MS = 6000

const useGameSocket = (roomCode) => {
  const setGameState = useGameStore((state) => state.setGameState)
  const token = useAuthStore((state) => state.token)
  const wsRef = useRef(null)
  const lastSeqRef = useRef(-1)
  const reconnectAttemptRef = useRef(0)
  const reconnectTimerRef = useRef(null)
  const shouldReconnectRef = useRef(true)
  const pingIntervalRef = useRef(null)
  const pongTimeoutRef = useRef(null)

  // 'connecting' | 'connected' | 'reconnecting' | 'disconnected'
  const [connectionStatus, setConnectionStatus] = useState('connecting')

  useEffect(() => {
    if (!roomCode || !token) return

    shouldReconnectRef.current = true
    lastSeqRef.current = -1
    reconnectAttemptRef.current = 0

    function stopHeartbeat() {
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current)
        pingIntervalRef.current = null
      }
      if (pongTimeoutRef.current) {
        clearTimeout(pongTimeoutRef.current)
        pongTimeoutRef.current = null
      }
    }

    // Level 2 fallback, and also our recovery path for a stale-snapshot
    // regression (see onmessage below): a single REST call to the existing
    // state endpoint re-establishes ground truth, whichever direction the
    // local sequence_number was off in.
    async function resyncViaRest() {
      try {
        const res = await fetch(`${API_URL}/rooms/${roomCode}/state`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        if (!res.ok) {
          console.error('WS resync REST call failed:', res.status)
          return
        }
        const data = await res.json()
        lastSeqRef.current = data.sequence_number
        setGameState(data)
        console.log('WS resynced via REST, sequence_number:', data.sequence_number)
      } catch (error) {
        console.error('WS resync REST error:', error)
      }
    }

    function connect() {
      setConnectionStatus(reconnectAttemptRef.current === 0 ? 'connecting' : 'reconnecting')

      const ws = new WebSocket(`${WS_URL}/ws/${roomCode}?token=${encodeURIComponent(token)}`)
      wsRef.current = ws

      ws.onopen = () => {
        reconnectAttemptRef.current = 0
        setConnectionStatus('connected')

        // Start the heartbeat - connection open.
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState !== WebSocket.OPEN) return

          ws.send(JSON.stringify({ type: 'ping' }))

          // Level 1: if no pong arrives within the timeout, the connection is genuinely dead (the classic zombie case)
          // - force-close it ourselves and let the existing reconnect logic take over.
          pongTimeoutRef.current = setTimeout(() => {
            console.log('WS no pong received in time, forcing close')
            ws.close()
          }, PONG_TIMEOUT_MS)
        }, PING_INTERVAL_MS)
      }

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)

        if (data.type === 'pong') {
          // connection response: clear suspect timeout
          if (pongTimeoutRef.current) clearTimeout(pongTimeoutRef.current)

          // Any mismatch - server ahead (a broadcast was silently dropped,
          // the original level-2 case) or server behind (a rare but real
          // case: the backend recovered a room from a stale Postgres
          // snapshot after a Redis-only crash, so its sequence_number
          // regressed below what we already applied) - means our local
          // number can no longer be trusted either way. Resync via REST
          // rather than trying to reason about which direction it's off.
          if (data.sequence_number !== lastSeqRef.current) {
            console.log('WS pong reports mismatched sequence_number, resyncing via REST:', data.sequence_number)
            resyncViaRest()
          }
          return
        }

        if (data.sequence_number === lastSeqRef.current) {
          console.log('WS ignored duplicate message:', data.sequence_number)
          return
        }

        if (data.sequence_number < lastSeqRef.current) {
          // A genuine regression, not a duplicate: on an already-open
          // connection the sequence_number should never move backwards
          // during normal operation. If it does, the server itself has
          // gone "back in time" (stale-snapshot recovery) - our local
          // state is no longer trustworthy as a reference point, so we
          // resync instead of silently discarding this as stale.
          console.log('WS detected sequence regression, resyncing via REST:', data.sequence_number)
          resyncViaRest()
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
        stopHeartbeat()

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
      stopHeartbeat()
      if (wsRef.current) wsRef.current.close()
      setConnectionStatus('disconnected')
    }
  }, [roomCode, token])

  return { wsRef, connectionStatus }
}

export default useGameSocket
