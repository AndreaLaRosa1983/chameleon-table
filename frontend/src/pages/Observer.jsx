import { useNavigate, useParams } from 'react-router-dom'
import { COLOR_ASSETS, CARD_TYPE_ASSETS, CARD_LG_H } from '../constants'
import { MOCK_STATE } from '../mocks/mockData'
import s from './Game.module.scss'
import useGameStore from '../store/useGameStore'
import useAuthStore from '../store/useAuthStore'
import useGameSocket from '../hooks/useGameSocket'
function cardAsset(card) {
  if (!card) return null
  if (card.card_type === 'color') return COLOR_ASSETS[card.color] || null
  return CARD_TYPE_ASSETS[card.card_type] || null
}

function groupCards(cards) {
  const counts = {}
  for (const c of cards) {
    if (c.card_type === 'color' && c.color) {
      counts[c.color] = (counts[c.color] || 0) + 1
    }
  }
  return counts
}

function hasPlus2(cards) { return cards.some(c => c.card_type === 'plus2') }
function countPlus2(cards) { return cards.filter(c => c.card_type === 'plus2').length }

function ColorChip({ color, count, size = 'sm' }) {
  return (
    <div className={s.colorChip}>
      <img src={COLOR_ASSETS[color]} alt={color} className={`${s.cardImg} ${s[size]}`} />
      <span className={s.chipCount}>{count}</span>
    </div>
  )
}

function Plus2Chip({ count, size = 'sm' }) {
  return (
    <div className={s.colorChip}>
      <img src="/assets/cotton.png" alt="+2" className={`${s.cardImg} ${s[size]}`} />
      <span className={s.chipCount}>{count}</span>
    </div>
  )
}

function PlayerCards({ cards, size = 'sm' }) {
  const colorCounts = groupCards(cards)
  const plus2 = hasPlus2(cards)
  const plus2Count = countPlus2(cards)
  return (
    <div className={s.playerCards}>
      {Object.entries(colorCounts).map(([color, count]) => (
        <ColorChip key={color} color={color} count={count} size={size} />
      ))}
      {plus2 && <Plus2Chip count={plus2Count} size={size} />}
    </div>
  )
}

function PlayerPanel({ player, isTurn, className = '', cardSize = 'sm' }) {
  return (
    <div className={`${s.playerPanel} ${isTurn ? s.isTurn : ''} ${className}`}>
      <div className={`${s.playerName} ${isTurn ? s.isTurn : ''}`}>
        {isTurn && <span className={s.turnDot} />}
        {player.name}
        {player.passed && <span className={s.passedBadge}>passed</span>}
      </div>
      <PlayerCards cards={player.cards} size={cardSize} />
    </div>
  )
}

function StackedRowCards({ cards }) {
  if (cards.length === 0) {
    return <span className={s.emptyRow}>empty</span>
  }
  return (
    <div className={s.stackedCards}>
      {cards.map((card, i) => (
        <img
          key={i}
          src={cardAsset(card)}
          alt={card.color || '+2'}
          className={s.stackedCard}
          style={{ marginTop: i === 0 ? 0 : `${-CARD_LG_H * 0.55}px` }}
        />
      ))}
    </div>
  )
}

function RowPanel({ row, index }) {
  return (
    <div className={`${s.rowPanel} ${row.taken_by ? s.taken : ''}`}>
      <span className={s.rowLabel}>
        {index + 1}
        {row.taken_by && <span className={s.takenBy}>· {row.taken_by}</span>}
      </span>
      {!row.taken_by && <StackedRowCards cards={row.cards} />}
    </div>
  )
}

function DeckPanel({ count, lastRound }) {
  return (
    <div className={`${s.deckPanel} ${lastRound ? s.lastRound : ''}`}>
      <img
        src="/assets/back.png"
        alt="deck"
        className={`${s.cardImg} ${s.md}`}
        style={{ borderRadius: 8 }}
      />
      <span className={`${s.deckCount} ${lastRound ? s.lastRound : ''}`}>{count}</span>
      <span className={s.deckLabel}>{lastRound ? 'last round' : 'cards'}</span>
    </div>
  )
}

export default function Observer() {
  const { roomCode } = useParams()
  const { gameState: liveState } = useGameStore()
  const { username } = useAuthStore()

  const gameState = liveState ?? MOCK_STATE

  useGameSocket(roomCode)
  
  const players = gameState.players
  const mainPlayer = players[0]
  const others = players.slice(1)

  const topOthers = others.length >= 3 ? others.slice(2) : []
  const leftOther = others[0] || null
  const rightOther = others[1] || null

  return (
    <div className={s.gameTable}>

      <div className={s.header}>
        <span className={s.roomCode}>{gameState.room_code ?? roomCode} · observing</span>
        <span className={`${s.turnInfo} ${gameState.last_round ? s.lastRound : ''}`}>
          {gameState.last_round ? '⚑ last round' : `${gameState.current_turn}'s turn`}
        </span>
      </div>

      {topOthers.length > 0 && (
        <div className={s.topOpponents}>
          {topOthers.map(p => (
            <PlayerPanel key={p.name} player={p} isTurn={gameState.current_turn === p.name} className={s.flex1} cardSize="sm" />
          ))}
        </div>
      )}

      <div className={s.middleSection}>
        {leftOther && (
          <div className={s.opponentSide}>
            <PlayerPanel player={leftOther} isTurn={gameState.current_turn === leftOther.name} className={s.fullHeight} cardSize="sm" />
          </div>
        )}

        <div className={s.rowsArea}>
          {gameState.rows.map((row, i) => (
            <RowPanel key={i} row={row} index={i} />
          ))}
        </div>

        {rightOther && (
          <div className={s.opponentSide}>
            <PlayerPanel player={rightOther} isTurn={gameState.current_turn === rightOther.name} className={s.fullHeight} cardSize="sm" />
          </div>
        )}
      </div>

      <div className={s.bottomSection}>
        <div className={s.myPanelWrapper}>
          {mainPlayer && (
            <PlayerPanel player={mainPlayer} isTurn={gameState.current_turn === mainPlayer.name} cardSize="md" />
          )}
        </div>

        <DeckPanel count={gameState.deck_count} lastRound={gameState.last_round} />
      </div>

    </div>
  )
}