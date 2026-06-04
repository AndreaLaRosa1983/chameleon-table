import { useState } from 'react'

// !!! mock attenzione

const MOCK_STATE = {
  room_code: 'BEJDDL',
  phase: 'playing',
  current_turn: 'Alice',
  deck_count: 54,
  last_round: false,
  pending_card: null,
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

function Card({ color, size = 'sm', style = {} }) {
  const s = size === 'lg' ? CARD_LG : size === 'md' ? CARD_MD : CARD_SM
  return (
    <img
      src={COLOR_ASSETS[color] || COLOR_ASSETS.cotton}
      alt={color}
      style={{ width: s.w, height: s.h, borderRadius: 6, border: '0.5px solid rgba(0,0,0,0.2)', objectFit: 'contain', flexShrink: 0, ...style }}
    />
  )
}

function ColorChip({ color, count, size = 'sm' }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <Card color={color} size={size} />
      <span style={{ fontSize: 12, fontWeight: 700, color: 'rgba(255,255,255,0.7)' }}>{count}</span>
    </div>
  )
}

function Plus2Chip({ count, isMe, size = 'sm' }) {
  const s = size === 'lg' ? CARD_LG : size === 'md' ? CARD_MD : CARD_SM
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

function RowPanel({ row, index, canTake, onTake }) {
  const clickable = canTake && row.cards.length > 0 && !row.taken_by
  return (
    <div
      onClick={clickable ? onTake : undefined}
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

function DeckPanel({ count, lastRound }) {
  return (
    <div style={{
      background: 'rgba(0,0,0,0.25)',
      border: lastRound ? '2px solid #E24B4A' : '1px solid rgba(255,255,255,0.1)',
      borderRadius: 14,
      padding: '14px 16px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 8,
      flexShrink: 0,
      width: 100,
    }}>
      <img src="/assets/back.png" alt="deck" style={{ width: CARD_MD.w, height: CARD_MD.h, borderRadius: 8, border: '0.5px solid rgba(0,0,0,0.2)', objectFit: 'contain' }} />
      <span style={{ fontSize: 18, fontWeight: 700, color: lastRound ? '#E24B4A' : 'white' }}>{count}</span>
      <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>{lastRound ? 'last round' : 'cards'}</span>
    </div>
  )
}

export default function Game() {
  const [gameState] = useState(MOCK_STATE)
  const myName = MY_NAME

  const me = gameState.players.find(p => p.name === myName)
  const opponents = gameState.players.filter(p => p.name !== myName)
  const isTurn = gameState.current_turn === myName

  const topOpponents = opponents.length >= 3 ? opponents.slice(2) : []
  const leftOpponent = opponents[0] || null
  const rightOpponent = opponents[1] || null

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

      {/* header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
        <span style={{ fontSize: 13, color: 'rgba(255,255,255,0.35)', letterSpacing: '0.1em' }}>
          {gameState.room_code}
        </span>
        <span style={{ fontSize: 13, color: gameState.last_round ? '#E24B4A' : 'rgba(255,255,255,0.35)' }}>
          {gameState.last_round ? '⚑ last round' : `${gameState.current_turn}'s turn`}
        </span>
      </div>

      {/* top opponents (4-5 players) */}
      {topOpponents.length > 0 && (
        <div style={{ display: 'flex', gap: 14, flexShrink: 0 }}>
          {topOpponents.map(p => (
            <PlayerPanel key={p.name} player={p} isMe={false} isTurn={gameState.current_turn === p.name} style={{ flex: 1 }} cardSize="sm" />
          ))}
        </div>
      )}

      {/* middle: left | rows | right */}
      <div style={{ display: 'flex', gap: 14, alignItems: 'stretch', flex: 1, minHeight: 0 }}>

        {leftOpponent && (
          <div style={{ flex: '0 0 180px' }}>
            <PlayerPanel player={leftOpponent} isMe={false} isTurn={gameState.current_turn === leftOpponent.name} style={{ height: '100%', boxSizing: 'border-box' }} cardSize="sm" />
          </div>
        )}

        <div style={{ flex: 1, display: 'flex', gap: 14, minHeight: 0 }}>
          {gameState.rows.map((row, i) => (
            <RowPanel key={i} row={row} index={i} canTake={isTurn && !gameState.pending_card} onTake={() => console.log('take row', i)} />
          ))}
        </div>

        {rightOpponent && (
          <div style={{ flex: '0 0 180px' }}>
            <PlayerPanel player={rightOpponent} isMe={false} isTurn={gameState.current_turn === rightOpponent.name} style={{ height: '100%', boxSizing: 'border-box' }} cardSize="sm" />
          </div>
        )}

      </div>

      {/* bottom: me + actions + deck */}
      <div style={{ display: 'flex', gap: 14, alignItems: 'flex-end', flexShrink: 0 }}>
        <div style={{ flex: 1 }}>
          <PlayerPanel player={me} isMe={true} isTurn={isTurn} cardSize="md" />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flexShrink: 0, justifyContent: 'flex-end' }}>
          {isTurn && !gameState.pending_card && (
            <button onClick={() => console.log('draw')} style={{
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
          )}
          {isTurn && gameState.pending_card && (
            <div style={{ padding: '12px 18px', background: 'rgba(60,100,140,0.3)', border: '1px solid rgba(100,160,200,0.3)', borderRadius: 10, color: '#a8c4d4', fontSize: 13, textAlign: 'center' }}>
              Choose a row
            </div>
          )}
        </div>

        <DeckPanel count={gameState.deck_count} lastRound={gameState.last_round} />
      </div>

    </div>
  )
}
