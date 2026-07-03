import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const useGameStore = create(
  persist(
    (set) => ({
      roomCode: null,
      gameState: null,

      setRoomCode: (code) => set({ roomCode: code }),
      setGameState: (state) => set({ gameState: state }),
      clearGameState: () => set({ gameState: null }),
      clearSession: () => set({ roomCode: null, gameState: null }),
    }),
    {
      name: 'chameleon-storage',
      partialize: (state) => ({
        roomCode: state.roomCode,
      }),
    }
  )
)

export default useGameStore