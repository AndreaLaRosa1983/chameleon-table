import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const useGameStore = create(
  persist(
    (set) => ({
      // per il   localStorage
      roomCode: null,
      playerName: null,
      token: null,

      // !!! questo lo metto solo in memoria NB 
      gameState: null,

      setRoomCode: (code) => set({ roomCode: code }),
      setPlayerName: (name) => set({ playerName: name }),
      setToken: (token) => set({ token }),
      setGameState: (state) => set({ gameState: state }),
      clearSession: () => set({ roomCode: null, playerName: null, token: null }),
    }),
    {
      name: 'chameleon-storage',
      partialize: (state) => ({
        // !!! controlla la persistenza se manca qualcosa
        roomCode: state.roomCode,
        playerName: state.playerName,
        token: state.token,
      }),
    }
  )
)

export default useGameStore