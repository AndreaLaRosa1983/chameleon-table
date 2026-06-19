import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const useGameStore = create(
  persist(
    (set) => ({
      roomCode: null,
      gameState: null,

      setRoomCode: (code) => set({ roomCode: code }),
      setGameState: (state) => set({ gameState: state }),
      clearSession: () => set({ roomCode: null }),
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