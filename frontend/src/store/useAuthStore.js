import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const useAuthStore = create(
  persist(
    (set) => ({
      token: null,
      username: null,

      setAuth: (token, username) => set({ token, username }),
      clearAuth: () => set({ token: null, username: null }),
    }),
    {
      name: 'chameleon-auth-storage',
    }
  )
)

export default useAuthStore