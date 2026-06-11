import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import useGameStore from '../store/useGameStore'
import useGameSocket from '../hooks/useGameSocket'
import { drawCard, placeCard, takeRow } from '../api/api'
import s from './Game.module.scss'

const MOCK_STATE = {
  room_code: 'BEJDDL',
  phase: 'playing',
  current_turn: 'Bob',
  deck_count: 54,
  last_round: false,
  pending_card: { card_type: 'color', color: 'green' },
  turn_order: ['Alice', 'Bob', 'Charles', 'David', 'Eve'],
  rows: [
    { cards: [{ card_type: 'color', color: 'green' }, { card_type: 'color', color: 'green' }, { card_type: 'color', color: 'blue' }], taken_by: null, max_cards: 3 },
    { cards: [{ card_type: 'color', color: 'red' }], taken_by: null, max_cards: 3 },
    { cards: [], taken_by: null, max_cards: 3 },
  ],
  players: [
    { name: 'Alice',   cards: [{ card_type: 'color', color: 'yellow' }, { card_type: 'color', color: 'yellow' }, { card_type: 'color', color: 'brown' }, { card_type: 'color', color: 'brown' }], jokers: [], passed: false, active: true },
    { name: 'Bob',     cards: [{ card_type: 'color', color: 'blue' }, { card_type: 'color', color: 'blue' }, { card_type: 'color', color: 'orange' }, { card_type: 'plus2', color: null }, { card_type: 'plus2', color: null }], jokers: [], passed: false, active: true },
    { name: 'Charles', cards: [{ card_type: 'color', color: 'green' }, { card_type: 'color', color: 'green' }, { card_type: 'color', color: 'red' }, { card_type: 'plus2', color: null }], jokers: [], passed: false, active: true },
    { name: 'David',   cards: [{ card_type: 'color', color: 'purple' }, { card_type: 'color', color: 'orange' }], jokers: [], passed: true, active: true },
    { name: 'Eve',     cards: [{ card_type: 'color', color: 'brown' }, { card_type: 'color', color: 'yellow' }], jokers: [], passed: false, active: true },
  ],
}

const MY_NAME = 'Bob'

const COLOR_ASSETS = {
  green:  '/assets/green.png',
  blue:   '/assets/blue.png',
  red:    '/assets/red.png',
  yellow: '/assets/yellow.png',
  brown:  '/assets/brown.png',
  purple: '/assets/purple.png',
  orange: '/assets/orange.png',
  cotton: '/assets/cotton.png',
}

const CARD_MD_W = 80
const CARD_MD_H = 112
const CARD_LG_W = 110
const CARD_LG_H = 154

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
  if (card.card_type === 'plus2') return '/assets/cotton.png'
  return COLOR_ASSETS[card.color] || null
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

function PlayerCards({ cards, isMe, size = 'sm' }) {
  const colorCounts = groupCards(cards)
  const plus2 = hasPlus2(cards)
  const plus2Count = countPlus2(cards)
  return (
    <div className={s.playerCards}>
      {Object.entries(colorCounts).map(([color, count]) => (
        <ColorChip key={color} color={color} count={count} size={size} />
      ))}
      {plus2 && <Plus2Chip count={plus2Count} isMe={isMe} size={size} />}
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
      <PlayerCards cards={player.cards} isMe={isMe} size={cardSize} />
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
          src={card.card_type === 'plus2' ? '/assets/cotton.png' : COLOR_ASSETS[card.color]}
          alt={card.color || '+2'}
          className={s.stackedCard}
          style={{ marginTop: i === 0 ? 0 : `${-CARD_LG_H * 0.55}px` }}
        />
      ))}
    </div>
  )
}

function RowPanel({ row, index, canPlace, onPlace, canTake, onTake, forceTake }) {
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

export default function Game() {
  const { roomCode, playerName, gameState: liveState } = useGameStore()
  const [confirmRow, setConfirmRow] = useState(null)
  const navigate = useNavigate()

  const gameState = liveState ?? MOCK_STATE
  const myName = playerName ?? MY_NAME

  useGameSocket(roomCode, playerName)

  useEffect(() => {
    if (gameState?.phase === 'finished' || gameState?.phase === 'aborted') {
      navigate(`/results/${roomCode}`)
    }
  }, [gameState?.phase])

  const me = gameState.players.find(p => p.name === myName)
  const opponents = gameState.players.filter(p => p.name !== myName)
  const isTurn = gameState.current_turn === myName
  const hasPending = !!gameState.pending_card
  const hasAvailableRow = gameState.rows.some(r => !r.taken_by && r.cards.length < r.max_cards)
  const forceTake = isTurn && hasPending && !hasAvailableRow

  const topOpponents = opponents.length >= 3 ? opponents.slice(2) : []
  const leftOpponent = opponents[0] || null
  const rightOpponent = opponents[1] || null

  async function handleDraw() {
    try { await drawCard(roomCode, myName) }
    catch (e) { console.error('draw error:', e) }
  }

  function handlePlaceRequest(rowIndex) { setConfirmRow(rowIndex) }

  async function handlePlaceConfirm() {
    try { await placeCard(roomCode, myName, confirmRow) }
    catch (e) { console.error('place error:', e) }
    setConfirmRow(null)
  }

  function handlePlaceCancel() { setConfirmRow(null) }

  async function handleTakeRow(rowIndex) {
    try { await takeRow(roomCode, myName, rowIndex) }
    catch (e) { console.error('take row error:', e) }
  }

  return (
    <div className={s.gameTable}>

      {confirmRow !== null && (
        <ConfirmModal rowIndex={confirmRow} onConfirm={handlePlaceConfirm} onCancel={handlePlaceCancel} />
      )}

      <div className={s.header}>
        <span className={s.roomCode}>{gameState.room_code}</span>
        <span className={`${s.turnInfo} ${gameState.last_round ? s.lastRound : ''}`}>
          {gameState.last_round ? '⚑ last round' : `${gameState.current_turn}'s turn`}
        </span>
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
