import { useNavigate, useParams } from 'react-router-dom'
import useGameStore from '../store/useGameStore'
import s from './Results.module.scss'

const COLOR_ASSETS = {
  green:  '/assets/green.png',
  blue:   '/assets/blue.png',
  red:    '/assets/red.png',
  yellow: '/assets/yellow.png',
  brown:  '/assets/brown.png',
  purple: '/assets/purple.png',
  orange: '/assets/orange.png',
}

const MOCK_SCORES = {
  Alice:   28,
  Bob:     21,
  Charles: 14,
  David:   11,
  Eve:     4,
}

const MOCK_GAME_STATE = {
  phase: 'finished',
  players: [
    { name: 'Alice',   cards: [{ card_type: 'color', color: 'yellow' }, { card_type: 'color', color: 'yellow' }, { card_type: 'color', color: 'yellow' }, { card_type: 'color', color: 'yellow' }, { card_type: 'color', color: 'brown' }, { card_type: 'color', color: 'brown' }, { card_type: 'plus2' }, { card_type: 'plus2' }], left: false },
    { name: 'Bob',     cards: [{ card_type: 'color', color: 'green' }, { card_type: 'color', color: 'green' }, { card_type: 'color', color: 'green' }, { card_type: 'color', color: 'green' }, { card_type: 'color', color: 'green' }, { card_type: 'color', color: 'orange' }, { card_type: 'color', color: 'orange' }], left: false },
    { name: 'Charles', cards: [{ card_type: 'color', color: 'red' }, { card_type: 'color', color: 'red' }, { card_type: 'color', color: 'red' }, { card_type: 'color', color: 'blue' }, { card_type: 'color', color: 'blue' }], left: false },
    { name: 'David',   cards: [{ card_type: 'color', color: 'purple' }, { card_type: 'color', color: 'purple' }, { card_type: 'color', color: 'purple' }, { card_type: 'color', color: 'purple' }, { card_type: 'color', color: 'orange' }], left: false },
    { name: 'Eve',     cards: [{ card_type: 'color', color: 'brown' }, { card_type: 'color', color: 'brown' }, { card_type: 'color', color: 'red' }], left: false },
  ],
}

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

  const state = gameState ?? MOCK_GAME_STATE
  const phase = state.phase
  const players = state.players

  const scores = MOCK_SCORES

  const ranked = [...players]
    .filter(p => !p.left)
    .sort((a, b) => (scores[b.name] ?? 0) - (scores[a.name] ?? 0))

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
