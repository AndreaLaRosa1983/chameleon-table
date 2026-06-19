import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../store/useAuthStore'
import { login, register } from '../api/api'
import CardCarousel from '../components/CardCarousel'
import s from './Auth.module.scss'

function Auth() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((state) => state.setAuth)

  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const isLogin = mode === 'login'

  const switchMode = () => {
    setMode(isLogin ? 'register' : 'login')
    setError(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!username || !password || (!isLogin && !email)) {
      setError('Please fill in all fields')
      return
    }
    setLoading(true)
    setError(null)
    try {
      if (isLogin) {
        const data = await login(username, password)
        setAuth(data.access_token, username)
        navigate('/')
      } else {
        await register(username, email, password)
        const data = await login(username, password)
        setAuth(data.access_token, username)
        navigate('/')
      }
    } catch (e) {
      setError(isLogin ? 'Invalid username or password' : 'Could not create account (username may already exist)')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={s.page}>
      <CardCarousel />

      <div className={s.formWrapper}>
        <div className={s.logo}>
          <div className={s.logoTitle}>🦎 Chameleon Table</div>
          <div className={s.logoSub}>online card game</div>
        </div>

        <form className={s.card} onSubmit={handleSubmit}>
          <div className={s.cardTitle}>{isLogin ? 'Sign in' : 'Create account'}</div>

          {error && <div className={s.error}>{error}</div>}

          <input
            className={s.input}
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
          />

          {!isLogin && (
            <input
              className={s.input}
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
            />
          )}

          <input
            className={s.input}
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={isLogin ? 'current-password' : 'new-password'}
          />

          <button className={s.btnPrimary} type="submit" disabled={loading}>
            {loading ? (isLogin ? 'Signing in…' : 'Creating account…') : (isLogin ? 'Sign in' : 'Create account')}
          </button>

          <div className={s.switchLink}>
            {isLogin ? (
              <>Don't have an account? <button type="button" onClick={switchMode}>Register</button></>
            ) : (
              <>Already have an account? <button type="button" onClick={switchMode}>Sign in</button></>
            )}
          </div>
        </form>
      </div>
    </div>
  )
}

export default Auth