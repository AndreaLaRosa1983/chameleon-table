import { useNavigate, useParams } from 'react-router-dom'
import useGameStore from '../store/useGameStore'
import { COLOR_ASSETS } from '../constants'
import { MOCK_FINISHED_STATE, MOCK_ABORTED_STATE, MOCK_SCORES } from '../mocks/mockData'
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

  // fall back to mock state when navigating directly to /results/:roomCode
  const state = gameState ?? MOCK_FINISHED_STATE
  const phase = state.phase
  const players = state.players

  // TODO: replace with real scores from backend once /rooms/{code}/scores exists
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