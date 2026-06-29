import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import useGameStore from '../store/useGameStore'
import { COLOR_ASSETS, CARD_TYPE_ASSETS } from '../constants'
import { MOCK_FINISHED_STATE } from '../mocks/mockData'
import { getScores } from '../api/api'
import s from './Results.module.scss'

function groupColorCards(cards) {
  const counts = {}
  for (const c of cards) {
    if (c.card_type === 'color' && c.color) {
      counts[c.color] = (counts[c.color] || 0) + 1
    }
  }
  return counts
}

function countPlus2(cards) {
  return cards.filter(c => c.card_type === 'plus2').length
}

function PlayerRow({ player, rank, score }) {
  const isWinner = rank === 1
  const colorCounts = groupColorCards(player.cards)
  const plus2Count = countPlus2(player.cards)
  const jokerCount = player.jokers?.length ?? 0

  return (
    <div className={`${s.playerCard} ${isWinner ? s.winner : ''}`}>
      {isWinner
        ? <div className={s.crown}>👑</div>
        : <div className={s.rank}>{rank}</div>
      }

      <div className={s.playerInfo}>
        <div className={s.playerName}>{player.name}</div>
        <div className={s.cardsRow}>
          {Object.entries(colorCounts).map(([color, count]) => (
            <div key={color} className={s.colorChip}>
              <img src={COLOR_ASSETS[color]} alt={color} />
              <span>{count}</span>
            </div>
          ))}
          {plus2Count > 0 && (
            <div className={s.colorChip}>
              <img src="/assets/cotton.png" alt="+2" />
              <span>{plus2Count}</span>
            </div>
          )}
          {jokerCount > 0 && (
            <div className={s.colorChip}>
              <img src={CARD_TYPE_ASSETS['joker']} alt="joker" />
              <span>{jokerCount}</span>
            </div>
          )}
        </div>
      </div>

      <div className={s.scoreWrapper}>
        <div className={s.playerScore}>{score}</div>
        <div className={s.scoreLabel}>points</div>
      </div>
    </div>
  )
}

export default function Results() {
  const navigate = useNavigate()
  const { roomCode } = useParams()
  const { gameState, clearSession } = useGameStore()
  const [scores, setScores] = useState(null)

  const state = gameState ?? MOCK_FINISHED_STATE
  const phase = state.phase
  const players = state.players
  console.log('players jokers:', players.map(p => ({name: p.name, jokers: p.jokers})))
  useEffect(() => {
    if (phase === 'finished' && roomCode) {
      getScores(roomCode)
        .then(setScores)
        .catch(e => console.error('Error fetching scores:', e))
    }
  }, [phase, roomCode])

  const ranked = scores
    ? [...players]
        .filter(p => !p.left)
        .sort((a, b) => (scores[b.name] ?? 0) - (scores[a.name] ?? 0))
    : []

  function handleHome() {
    clearSession()
    navigate('/')
  }

  return (
    <div className={s.page}>
      <div className={s.title}>
        {phase === 'aborted' ? 'Game Aborted' : 'Game Over'}
      </div>
      <div className={s.subtitle}>ROOM · {roomCode}</div>

      {phase === 'aborted' ? (
        <div className={s.abortedMessage}>
          The game was interrupted because too many players disconnected.
        </div>
      ) : scores === null ? (
        <div className={s.loading}>Loading scores...</div>
      ) : (
        <div className={s.playersColumn}>
          {ranked.map((player, i) => (
            <PlayerRow
              key={player.name}
              player={player}
              rank={i + 1}
              score={scores[player.name] ?? 0}
            />
          ))}
        </div>
      )}

      <button className={s.homeBtn} onClick={handleHome}>
        Back to Home
      </button>
    </div>
  )
}