import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import useGameStore from '../store/useGameStore'
import useAuthStore from '../store/useAuthStore'
import useGameSocket from '../hooks/useGameSocket'
import { drawCard, placeCard, takeRow, leaveRoom } from '../api/api'
import { COLOR_ASSETS, CARD_TYPE_ASSETS, CARD_LG_H } from '../constants'
import { MY_NAME, MOCK_STATE } from '../mocks/mockData'
import s from './Game.module.scss'

const TURN_TIMEOUT_FALLBACK = 120

// Row-capacity corner icons. The "special" two-player layout has three rows
// with distinct capacities (1, 2, 3) and uses the green set; any other
// player count uses uniform rows of capacity 3 and the plain/brown icon.
const CAPACITY_ICON_NORMAL = '/assets/placeholder_3.png'
const CAPACITY_ICON_GREEN = {
  1: '/assets/placeholder_1_green.png',
  2: '/assets/placeholder_2_green.png',
  3: '/assets/placeholder_3_green.png',
}

function isSpecialTwoPlayerLayout(rows) {
  if (!rows || rows.length !== 3) return false
  const maxes = rows.map(r => r.max_cards).slice().sort((a, b) => a - b)
  return maxes[0] === 1 && maxes[1] === 2 && maxes[2] === 3
}

function capacityIcon(row, isSpecialLayout) {
  if (isSpecialLayout) return CAPACITY_ICON_GREEN[row.max_cards] || CAPACITY_ICON_NORMAL
  return CAPACITY_ICON_NORMAL
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

function cardAsset(card) {
  if (!card) return null
  if (card.card_type === 'color') return COLOR_ASSETS[card.color] || null
  return CARD_TYPE_ASSETS[card.card_type] || null
}

function TurnTimer({ timeLeft, total }) {
  const sliceSeconds = total / 6
  const activeSlices = Math.ceil(timeLeft / sliceSeconds)

  const sliceColors = [
    '#1D9E75',
    '#1D9E75',
    '#1D9E75',
    '#BA7517',
    '#BA7517',
    '#E24B4A',
  ]

  const slices = [
    "M0,0 L36,0 A36,36,0,0,0,18,-31.2 Z",
    "M0,0 L18,-31.2 A36,36,0,0,0,-18,-31.2 Z",
    "M0,0 L-18,-31.2 A36,36,0,0,0,-36,0 Z",
    "M0,0 L-36,0 A36,36,0,0,0,-18,31.2 Z",
    "M0,0 L-18,31.2 A36,36,0,0,0,18,31.2 Z",
    "M0,0 L18,31.2 A36,36,0,0,0,36,0 Z",
  ]

  return (
    <svg width="48" height="48" viewBox="0 0 80 80">
      <g transform="translate(40,40) rotate(-90)">
        {slices.map((d, i) => {
          const isActive = i >= (6 - activeSlices)
          return (
            <path
              key={i}
              d={d}
              fill={isActive ? sliceColors[i] : 'var(--color-border-tertiary)'}
              opacity={isActive ? 1 : 0.4}
              stroke="var(--color-background-primary)"
              strokeWidth="2"
            />
          )
        })}
        <circle r="14" fill="var(--color-background-primary)"/>
      </g>
    </svg>
  )
}

function ColorChip({ color, count, size = 'sm' }) {
  return (
    <div className={s.colorChip}>
      <img src={COLOR_ASSETS[color]} alt={color} className={`${s.cardImg} ${s[size]}`} />
      <span className={s.chipCount}>{count}</span>
    </div>
  )
}

function Plus2Chip({ count, isMe, size = 'sm' }) {
  return (
    <div className={s.colorChip}>
      <img src="/assets/cotton.png" alt="+2" className={`${s.cardImg} ${s[size]}`} />
      <span className={s.chipCount}>{isMe ? count : '?'}</span>
    </div>
  )
}

function JokerChip({ count, size = 'sm' }) {
  return (
    <div className={s.colorChip}>
      <img src={CARD_TYPE_ASSETS['joker']} alt="joker" className={`${s.cardImg} ${s[size]}`} />
      <span className={s.chipCount}>{count}</span>
    </div>
  )
}

function PlayerCards({ cards, jokers = [], isMe, size = 'sm' }) {
  const colorCounts = groupCards(cards)
  const plus2 = hasPlus2(cards)
  const plus2Count = countPlus2(cards)
  return (
    <div className={s.playerCards}>
      {Object.entries(colorCounts).map(([color, count]) => (
        <ColorChip key={color} color={color} count={count} size={size} />
      ))}
      {plus2 && <Plus2Chip count={plus2Count} isMe={isMe} size={size} />}
      {jokers.length > 0 && <JokerChip count={jokers.length} size={size} />}
    </div>
  )
}

function PlayerPanel({ player, isMe, isTurn, className = '', cardSize = 'sm' }) {
  return (
    <div className={`${s.playerPanel} ${isTurn ? s.isTurn : ''} ${className}`}>
      <div className={`${s.playerName} ${isTurn ? s.isTurn : ''}`}>
        {isTurn && <span className={s.turnDot} />}
        {isMe ? `You (${player.name})` : player.name}
        {player.passed && <span className={s.passedBadge}>passed</span>}
      </div>
      <PlayerCards cards={player.cards} jokers={player.jokers} isMe={isMe} size={cardSize} />
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

function RowPanel({ row, index, canPlace, onPlace, canTake, onTake, forceTake, isSpecialLayout }) {
  const clickablePlace = canPlace && !row.taken_by && row.cards.length < row.max_cards
  const clickableTake = (canTake || forceTake) && !row.taken_by && row.cards.length > 0
  const clickable = clickablePlace || clickableTake

  function handleClick() {
    if (clickablePlace) onPlace(index)
    else if (clickableTake) onTake(index)
  }

  return (
    <div
      onClick={clickable ? handleClick : undefined}
      className={`${s.rowPanel} ${row.taken_by ? s.taken : ''} ${clickable ? s.clickable : ''}`}
    >
      {!row.taken_by && (
        <img
          src={capacityIcon(row, isSpecialLayout)}
          alt={`max ${row.max_cards} cards`}
          title={`This row holds up to ${row.max_cards} card${row.max_cards > 1 ? 's' : ''}`}
          className={s.capacityIcon}
        />
      )}
      <span className={s.rowLabel}>
        {index + 1}
        {row.taken_by && <span className={s.takenBy}>· {row.taken_by}</span>}
      </span>
      {!row.taken_by && <StackedRowCards cards={row.cards} />}
    </div>
  )
}

function DeckPanel({ count, lastRound, canDraw, onDraw }) {
  return (
    <div
      onClick={canDraw ? onDraw : undefined}
      className={`${s.deckPanel} ${lastRound ? s.lastRound : canDraw ? s.canDraw : ''}`}
    >
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

function PendingCardPanel({ card, hasAvailableRow }) {
  if (!card) return null
  return (
    <div className={s.pendingCardPanel}>
      <span className={s.pendingLabel}>drawn card</span>
      <img src={cardAsset(card)} alt={card.color || '+2'} className={s.pendingCardImg} />
      <span className={`${s.pendingHint} ${!hasAvailableRow ? s.danger : ''}`}>
        {hasAvailableRow ? 'click a row to place' : 'take a row!'}
      </span>
    </div>
  )
}

function ConfirmModal({ rowIndex, onConfirm, onCancel }) {
  return (
    <div className={s.modalOverlay}>
      <div className={s.modalBox}>
        <span className={s.modalTitle}>Place card on row {rowIndex + 1}?</span>
        <div className={s.modalButtons}>
          <button onClick={onConfirm} className={s.btnConfirm}>Confirm</button>
          <button onClick={onCancel} className={s.btnCancel}>Cancel</button>
        </div>
      </div>
    </div>
  )
}

function LeaveModal({ onConfirm, onCancel }) {
  return (
    <div className={s.modalOverlay}>
      <div className={s.modalBox}>
        <span className={s.modalTitle}>Leave the game?</span>
        <span className={s.modalSubtitle}>You won't be able to rejoin.</span>
        <div className={s.modalButtons}>
          <button onClick={onConfirm} className={s.btnCancel}>Leave</button>
          <button onClick={onCancel} className={s.btnConfirm}>Stay</button>
        </div>
      </div>
    </div>
  )
}

export default function Game() {
  const { roomCode, gameState: liveState, clearSession } = useGameStore()
  const { username } = useAuthStore()
  const [confirmRow, setConfirmRow] = useState(null)
  const [showLeave, setShowLeave] = useState(false)
  const [timeLeft, setTimeLeft] = useState(TURN_TIMEOUT_FALLBACK)
  const navigate = useNavigate()

  const gameState = liveState ?? MOCK_STATE
  const myName = username ?? MY_NAME
  const totalTime = gameState.inactivity_timeout ?? TURN_TIMEOUT_FALLBACK

  useGameSocket(roomCode)

  if (!gameState || !gameState.players || gameState.players.length === 0) {
    return <div className={s.loading}>Loading...</div>
  }

  useEffect(() => {
    if (gameState?.phase === 'finished' || gameState?.phase === 'aborted') {
      navigate(`/results/${roomCode}`)
    }
  }, [gameState?.phase])

  useEffect(() => {
    const startedAt = gameState.turn_started_at

    function computeTimeLeft() {
      if (!startedAt) return totalTime
      const elapsed = Date.now() / 1000 - startedAt
      return Math.max(0, Math.ceil(totalTime - elapsed))
    }

    setTimeLeft(computeTimeLeft())
    const interval = setInterval(() => {
      setTimeLeft(computeTimeLeft())
    }, 1000)
    return () => clearInterval(interval)
  }, [gameState.current_turn, gameState.turn_started_at, totalTime])

  const me = gameState.players.find(p => p.name === myName)

  if (!me) {
    return <div className={s.loading}>Loading…</div>
  }

  const opponents = gameState.players.filter(p => p.name !== myName)
  const isTurn = gameState.current_turn === myName
  const hasPending = !!gameState.pending_card
  const hasAvailableRow = gameState.rows.some(r => !r.taken_by && r.cards.length < r.max_cards)
  const hasTakeableRow = gameState.rows.some(r => !r.taken_by && r.cards.length > 0)
  const forceTake = isTurn && hasPending && !hasAvailableRow
  const isSpecialLayout = isSpecialTwoPlayerLayout(gameState.rows)

  const topOpponents = opponents.length >= 3 ? opponents.slice(2) : []
  const leftOpponent = opponents[0] || null
  const rightOpponent = opponents[1] || null

  async function handleDraw() {
    try { await drawCard(roomCode) }
    catch (e) { console.error('draw error:', e) }
  }

  function handlePlaceRequest(rowIndex) { setConfirmRow(rowIndex) }

  async function handlePlaceConfirm() {
    try { await placeCard(roomCode, confirmRow) }
    catch (e) { console.error('place error:', e) }
    setConfirmRow(null)
  }

  function handlePlaceCancel() { setConfirmRow(null) }

  async function handleTakeRow(rowIndex) {
    try { await takeRow(roomCode, rowIndex) }
    catch (e) { console.error('take row error:', e) }
  }

  async function handleLeaveConfirm() {
    try {
      await leaveRoom(roomCode)
      clearSession()
      navigate('/')
    } catch (e) {
      console.error('leave error:', e)
    }
    setShowLeave(false)
  }

  return (
    <div className={s.gameTable}>

      {confirmRow !== null && (
        <ConfirmModal rowIndex={confirmRow} onConfirm={handlePlaceConfirm} onCancel={handlePlaceCancel} />
      )}

      {showLeave && (
        <LeaveModal onConfirm={handleLeaveConfirm} onCancel={() => setShowLeave(false)} />
      )}

      <div className={s.header}>
        <span className={s.roomCode}>{gameState.room_code}</span>
        <div className={s.headerCenter}>
          <span className={`${s.turnInfo} ${gameState.last_round ? s.lastRound : ''}`}>
            {gameState.last_round ? '⚑ last round' : `${gameState.current_turn}'s turn`}
          </span>
          {gameState.phase === 'playing' && (
            <TurnTimer timeLeft={timeLeft} total={totalTime} />
          )}
        </div>
        <button className={s.btnLeave} onClick={() => setShowLeave(true)}>Leave</button>
      </div>

      {topOpponents.length > 0 && (
        <div className={s.topOpponents}>
          {topOpponents.map(p => (
            <PlayerPanel key={p.name} player={p} isMe={false} isTurn={gameState.current_turn === p.name} className={s.flex1} cardSize="sm" />
          ))}
        </div>
      )}

      <div className={s.middleSection}>
        {leftOpponent && (
          <div className={s.opponentSide}>
            <PlayerPanel player={leftOpponent} isMe={false} isTurn={gameState.current_turn === leftOpponent.name} className={s.fullHeight} cardSize="sm" />
          </div>
        )}

        <div className={s.rowsArea}>
          {gameState.rows.map((row, i) => (
            <RowPanel
              key={i} row={row} index={i}
              canPlace={isTurn && hasPending && hasAvailableRow}
              canTake={isTurn && !hasPending}
              forceTake={forceTake}
              onTake={handleTakeRow}
              onPlace={handlePlaceRequest}
              isSpecialLayout={isSpecialLayout}
            />
          ))}
        </div>

        {rightOpponent && (
          <div className={s.opponentSide}>
            <PlayerPanel player={rightOpponent} isMe={false} isTurn={gameState.current_turn === rightOpponent.name} className={s.fullHeight} cardSize="sm" />
          </div>
        )}
      </div>

      <div className={s.bottomSection}>
        <div className={s.myPanelWrapper}>
          <PlayerPanel player={me} isMe={true} isTurn={isTurn} cardSize="md" />
        </div>

        {hasPending && <PendingCardPanel card={gameState.pending_card} hasAvailableRow={hasAvailableRow} />}

        {isTurn && !hasPending && (
          <div className={s.drawButtonWrapper}>
            <button
              onClick={hasAvailableRow ? handleDraw : undefined}
              className={`${s.drawButton} ${!hasAvailableRow ? s.disabled : ''}`}
            >
              Draw card
            </button>
            {hasAvailableRow && hasTakeableRow && (
              <span className={s.altActionHint}>or take a row with cards instead</span>
            )}
          </div>
        )}

        {isTurn && !hasPending && !hasAvailableRow && (
          <div className={s.takeRowWarning}>Take a row!</div>
        )}

        <DeckPanel
          count={gameState.deck_count}
          lastRound={gameState.last_round}
          canDraw={isTurn && !hasPending && hasAvailableRow}
          onDraw={handleDraw}
        />
      </div>

    </div>
  )
}
