import { useState } from 'react'
import useGameStore from '../store/useGameStore'
import useGameSocket from '../hooks/useGameSocket'

// ── MOCK DATA ──────────────────────────────────────────────────────────────────
const MOCK_STATE = {
  room_code: 'BEJDDL',
  phase: 'playing',
  current_turn: 'Bob',
  deck_count: 54,
  last_round: false,
  pending_card: { card_type: 'color', color: 'green' },
  turn_order: ['Alice', 'Bob', 'Charles', 'David', 'Eve'],
  rows: [
    { cards: [{ card_type: 'color', color: 'green' }, { card_type: 'color', color: 'green' }, { card_type: 'color', color: 'blue' }], taken_by: null },
    { cards: [{ card_type: 'color', color: 'red' }], taken_by: null },
    { cards: [], taken_by: null },
  ],
  players: [
    { name: 'Alice',   cards: [{ card_type: 'color', color: 'yellow' }, { card_type: 'color', color: 'yellow' }, { card_type: 'color', color: 'yellow' }, { card_type: 'color', color: 'yellow' }, { card_type: 'color', color: 'brown' }, { card_type: 'color', color: 'brown' }], jokers: [], passed: false, active: true },
    { name: 'Bob',     cards: [{ card_type: 'color', color: 'blue' }, { card_type: 'color', color: 'blue' }, { card_type: 'color', color: 'blue' }, { card_type: 'color', color: 'orange' }, { card_type: 'color', color: 'orange' }, { card_type: 'plus2', color: null }, { card_type: 'plus2', color: null }, { card_type: 'plus2', color: null }], jokers: [], passed: false, active: true },
    { name: 'Charles', cards: [{ card_type: 'color', color: 'green' }, { card_type: 'color', color: 'green' }, { card_type: 'color', color: 'green' }, { card_type: 'color', color: 'blue' }, { card_type: 'color', color: 'blue' }, { card_type: 'color', color: 'red' }, { card_type: 'plus2', color: null }], jokers: [], passed: false, active: true },
    { name: 'David',   cards: [{ card_type: 'color', color: 'purple' }, { card_type: 'color', color: 'purple' }, { card_type: 'color', color: 'purple' }, { card_type: 'color', color: 'purple' }, { card_type: 'color', color: 'purple' }, { card_type: 'color', color: 'orange' }], jokers: [], passed: true,  active: true },
    { name: 'Eve',     cards: [{ card_type: 'color', color: 'brown' }, { card_type: 'color', color: 'brown' }, { card_type: 'color', color: 'brown' }, { card_type: 'color', color: 'brown' }, { card_type: 'color', color: 'yellow' }, { card_type: 'color', color: 'yellow' }], jokers: [], passed: false, active: true },
  ],
}

const MY_NAME = 'Bob'

// ── HELPERS ────────────────────────────────────────────────────────────────────
const COLOR_ASSETS = {
  green: '/assets/green.png',
  blue: '/assets/blue.png',
  red: '/assets/red.png',
  yellow: '/assets/yellow.png',
  brown: '/assets/brown.png',
  purple: '/assets/purple.png',
  orange: '/assets/orange.png',
  cotton: '/assets/cotton.png',
}

const CARD_SM = { w: 52, h: 72 }
const CARD_MD = { w: 80, h: 112 }
const CARD_LG = { w: 110, h: 154 }

function groupCards(cards) {
  const counts = {}
  for (const c of cards) {
    if (c.card_type === 'color' && c.color) {
      counts[c.color] = (counts[c.color] || 0) + 1
    }
  }
  return counts
}

function hasPlus2(cards) {
  return cards.some(c => c.card_type === 'plus2')
}

function countPlus2(cards) {
  return cards.filter(c => c.card_type === 'plus2').length
}

function cardAsset(card) {
  if (!card) return null
  if (card.card_type === 'plus2') return '/assets/cotton.png'
  return COLOR_ASSETS[card.color] || null
}

// ── COMPONENTS ─────────────────────────────────────────────────────────────────

function ColorChip({ color, count, size = 'sm' }) {
  const s = size === 'md' ? CARD_MD : CARD_SM
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <img src={COLOR_ASSETS[color]} alt={color} style={{ width: s.w, height: s.h, borderRadius: 6, border: '0.5px solid rgba(0,0,0,0.2)', objectFit: 'contain', flexShrink: 0 }} />
      <span style={{ fontSize: 12, fontWeight: 700, color: 'rgba(255,255,255,0.7)' }}>{count}</span>
    </div>
  )
}

function Plus2Chip({ count, isMe, size = 'sm' }) {
  const s = size === 'md' ? CARD_MD : CARD_SM
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <img src="/assets/cotton.png" alt="+2" style={{ width: s.w, height: s.h, borderRadius: 6, border: '0.5px solid rgba(0,0,0,0.2)', objectFit: 'contain' }} />
      <span style={{ fontSize: 12, fontWeight: 700, color: 'rgba(255,255,255,0.7)' }}>{isMe ? count : '?'}</span>
    </div>
  )
}

function PlayerCards({ cards, isMe, size = 'sm' }) {
  const colorCounts = groupCards(cards)
  const plus2 = hasPlus2(cards)
  const plus2Count = countPlus2(cards)
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'flex-end' }}>
      {Object.entries(colorCounts).map(([color, count]) => (
        <ColorChip key={color} color={color} count={count} size={size} />
      ))}
      {plus2 && <Plus2Chip count={plus2Count} isMe={isMe} size={size} />}
    </div>
  )
}

function PlayerPanel({ player, isMe, isTurn, style = {}, cardSize = 'sm' }) {
  return (
    <div style={{
      background: 'rgba(0,0,0,0.25)',
      border: isTurn ? '2px solid #EF9F27' : '1px solid rgba(255,255,255,0.1)',
      borderRadius: 14,
      padding: '12px 16px',
      ...style,
    }}>
      <div style={{
        fontSize: 14, fontWeight: 700, marginBottom: 10,
        color: isTurn ? '#EF9F27' : 'rgba(255,255,255,1)',
        display: 'flex', alignItems: 'center', gap: 8,
      }}>
        {isTurn && <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#EF9F27', display: 'inline-block' }} />}
        {isMe ? `You (${player.name})` : player.name}
        {player.passed && (
          <span style={{ fontSize: 11, background: 'rgba(80,160,80,0.3)', color: '#90e090', padding: '2px 8px', borderRadius: 6 }}>
            passed
          </span>
        )}
      </div>
      <PlayerCards cards={player.cards} isMe={isMe} size={cardSize} />
    </div>
  )
}

function StackedRowCards({ cards }) {
  if (cards.length === 0) {
    return (
      <span style={{ fontSize: 13, color: 'rgba(255,255,255,0.25)', fontStyle: 'italic', margin: 'auto' }}>
        empty
      </span>
    )
  }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: CARD_LG.w + 8 }}>
      {cards.map((card, i) => (
        <img
          key={i}
          src={card.card_type === 'plus2' ? '/assets/cotton.png' : COLOR_ASSETS[card.color]}
          alt={card.color || '+2'}
          style={{
            width: CARD_LG.w, height: CARD_LG.h,
            borderRadius: 8,
            border: '0.5px solid rgba(0,0,0,0.2)',
            objectFit: 'contain',
            marginTop: i === 0 ? 0 : -CARD_LG.h * 0.55,
            boxShadow: i > 0 ? '0 -3px 8px rgba(0,0,0,0.3)' : 'none',
          }}
        />
      ))}
    </div>
  )
}

function RowPanel({ row, index, canPlace, onPlace }) {
  const clickable = canPlace && !row.taken_by && row.cards.length < 3
  return (
    <div
      onClick={clickable ? () => onPlace(index) : undefined}
      style={{
        flex: 1,
        background: row.taken_by ? 'rgba(0,0,0,0.15)' : 'rgba(0,0,0,0.25)',
        border: clickable ? '2px solid #EF9F27' : '1px solid rgba(255,255,255,0.1)',
        borderRadius: 14,
        padding: '14px 12px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        overflow: 'hidden',
        cursor: clickable ? 'pointer' : 'default',
        transition: 'border-color 0.15s, background 0.15s',
      }}
    >
      <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.3)', alignSelf: 'flex-start', marginBottom: 10 }}>
        {index + 1}
        {row.taken_by && <span style={{ marginLeft: 6, color: 'rgba(255,255,255,0.25)' }}>· {row.taken_by}</span>}
      </span>
      <StackedRowCards cards={row.cards} />
    </div>
  )
}

function DeckPanel({ count, lastRound, canDraw, onDraw }) {
  return (
    <div
      onClick={canDraw ? onDraw : undefined}
      style={{
        background: 'rgba(0,0,0,0.25)',
        border: lastRound ? '2px solid #E24B4A' : canDraw ? '2px solid #EF9F27' : '1px solid rgba(255,255,255,0.1)',
        borderRadius: 14,
        padding: '14px 16px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 8,
        flexShrink: 0,
        width: 100,
        cursor: canDraw ? 'pointer' : 'default',
        transition: 'border-color 0.15s',
      }}
    >
      <img src="/assets/back.png" alt="deck" style={{ width: CARD_MD.w, height: CARD_MD.h, borderRadius: 8, border: '0.5px solid rgba(0,0,0,0.2)', objectFit: 'contain' }} />
      <span style={{ fontSize: 18, fontWeight: 700, color: lastRound ? '#E24B4A' : 'white' }}>{count}</span>
      <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>{lastRound ? 'last round' : 'cards'}</span>
    </div>
  )
}

function PendingCardPanel({ card }) {
  if (!card) return null
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 8,
      flexShrink: 0,
    }}>
      <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', letterSpacing: '0.06em' }}>drawn card</span>
      <img
        src={cardAsset(card)}
        alt={card.color || '+2'}
        style={{
          width: CARD_MD.w, height: CARD_MD.h,
          borderRadius: 8,
          border: '2px solid #EF9F27',
          objectFit: 'contain',
          boxShadow: '0 0 16px rgba(239,159,39,0.3)',
        }}
      />
      <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>click a row to place</span>
    </div>
  )
}

function ConfirmModal({ rowIndex, onConfirm, onCancel }) {
  return (
    <div style={{
      position: 'fixed', inset: 0,
      background: 'rgba(0,0,0,0.6)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 100,
    }}>
      <div style={{
        background: '#1e3020',
        border: '1px solid rgba(255,255,255,0.15)',
        borderRadius: 16,
        padding: '28px 36px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 20,
        minWidth: 260,
      }}>
        <span style={{ fontSize: 16, color: 'white', fontWeight: 600 }}>
          Place card on row {rowIndex + 1}?
        </span>
        <div style={{ display: 'flex', gap: 12 }}>
          <button
            onClick={onConfirm}
            style={{
              padding: '10px 28px',
              background: 'rgba(80,140,80,0.35)',
              border: '1px solid rgba(120,200,120,0.4)',
              borderRadius: 10,
              color: '#a8e0a8',
              fontSize: 14,
              fontFamily: 'inherit',
              cursor: 'pointer',
            }}
          >
            Confirm
          </button>
          <button
            onClick={onCancel}
            style={{
              padding: '10px 28px',
              background: 'rgba(140,60,60,0.3)',
              border: '1px solid rgba(200,100,100,0.3)',
              borderRadius: 10,
              color: '#e0a8a8',
              fontSize: 14,
              fontFamily: 'inherit',
              cursor: 'pointer',
            }}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}

// ── MAIN ───────────────────────────────────────────────────────────────────────
export default function Game() {
  const { roomCode, playerName, gameState: liveState } = useGameStore()
  const [confirmRow, setConfirmRow] = useState(null)

  // fall back to mock when navigating directly to /game/MOCK
  const gameState = liveState ?? MOCK_STATE
  const myName = playerName ?? MY_NAME

  useGameSocket(roomCode, playerName)

  const me = gameState.players.find(p => p.name === myName)
  const opponents = gameState.players.filter(p => p.name !== myName)
  const isTurn = gameState.current_turn === myName
  const hasPending = !!gameState.pending_card

  const topOpponents = opponents.length >= 3 ? opponents.slice(2) : []
  const leftOpponent = opponents[0] || null
  const rightOpponent = opponents[1] || null

  function handleDraw() {
    console.log("draw card - TODO: call POST /draw")
  }

  function handlePlaceRequest(rowIndex) {
    setConfirmRow(rowIndex)
  }

  function handlePlaceConfirm() {
    console.log("place card on row", confirmRow, "- TODO: call POST /place")
    setConfirmRow(null)
  }

  function handlePlaceCancel() {
    setConfirmRow(null)
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: 14,
      padding: '14px 20px',
      height: '100vh',
      overflow: 'hidden',
      width: '100%',
      boxSizing: 'border-box',
      background: '#1a2a1a',
      fontFamily: "'Georgia', serif",
    }}>

      {/* confirm modal */}
      {confirmRow !== null && (
        <ConfirmModal
          rowIndex={confirmRow}
          onConfirm={handlePlaceConfirm}
          onCancel={handlePlaceCancel}
        />
      )}

      {/* header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
        <span style={{ fontSize: 13, color: 'rgba(255,255,255,0.35)', letterSpacing: '0.1em' }}>
          {gameState.room_code}
        </span>
        <span style={{ fontSize: 13, color: gameState.last_round ? '#E24B4A' : 'rgba(255,255,255,0.35)' }}>
          {gameState.last_round ? '⚑ last round' : `${gameState.current_turn}'s turn`}
        </span>
      </div>

      {/* top opponents */}
      {topOpponents.length > 0 && (
        <div style={{ display: 'flex', gap: 14, flexShrink: 0 }}>
          {topOpponents.map(p => (
            <PlayerPanel key={p.name} player={p} isMe={false} isTurn={gameState.current_turn === p.name} style={{ flex: 1 }} cardSize="sm" />
          ))}
        </div>
      )}

      {/* middle */}
      <div style={{ display: 'flex', gap: 14, alignItems: 'stretch', flex: 1, minHeight: 0 }}>

        {leftOpponent && (
          <div style={{ flex: '0 0 180px' }}>
            <PlayerPanel player={leftOpponent} isMe={false} isTurn={gameState.current_turn === leftOpponent.name} style={{ height: '100%', boxSizing: 'border-box' }} cardSize="sm" />
          </div>
        )}

        <div style={{ flex: 1, display: 'flex', gap: 14, minHeight: 0 }}>
          {gameState.rows.map((row, i) => (
            <RowPanel
              key={i}
              row={row}
              index={i}
              canPlace={isTurn && hasPending}
              onPlace={handlePlaceRequest}
            />
          ))}
        </div>

        {rightOpponent && (
          <div style={{ flex: '0 0 180px' }}>
            <PlayerPanel player={rightOpponent} isMe={false} isTurn={gameState.current_turn === rightOpponent.name} style={{ height: '100%', boxSizing: 'border-box' }} cardSize="sm" />
          </div>
        )}

      </div>

      {/* bottom */}
      <div style={{ display: 'flex', gap: 14, alignItems: 'flex-end', flexShrink: 0 }}>

        <div style={{ flex: 1 }}>
          <PlayerPanel player={me} isMe={true} isTurn={isTurn} cardSize="md" />
        </div>

        {/* pending card */}
        {hasPending && <PendingCardPanel card={gameState.pending_card} />}

        {/* draw button (only when it's your turn and no pending) */}
        {isTurn && !hasPending && (
          <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', flexShrink: 0 }}>
            <button onClick={handleDraw} style={{
              padding: '12px 24px',
              background: 'rgba(80,140,80,0.3)',
              border: '1px solid rgba(120,200,120,0.4)',
              borderRadius: 10,
              color: '#a8e0a8',
              fontSize: 14,
              fontFamily: 'inherit',
              cursor: 'pointer',
              letterSpacing: '0.04em',
            }}>
              Draw card
            </button>
          </div>
        )}

        <DeckPanel
          count={gameState.deck_count}
          lastRound={gameState.last_round}
          canDraw={isTurn && !hasPending}
          onDraw={handleDraw}
        />
      </div>

    </div>
  )
}
