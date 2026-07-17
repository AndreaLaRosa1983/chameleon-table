import { useNavigate } from 'react-router-dom'
import s from './Rules.module.scss'

const SCORE_TABLE = [
  { cards: 1, points: 1 },
  { cards: 2, points: 3 },
  { cards: 3, points: 6 },
  { cards: 4, points: 10 },
  { cards: 5, points: 15 },
  { cards: '6+', points: 21 },
]

function Rules() {
  const navigate = useNavigate()

  return (
    <div className={s.page}>

      <div className={s.logo}>
            <div className={s.logoTitle}>
                 <img src="/assets/chameleon-logo.svg" alt="" className={s.logoIcon} />
               Chameleon Table
             </div>
        <div className={s.logoSub}>how to play</div>
      </div>

      <button className={s.btnBack} onClick={() => navigate(-1)}>← Back</button>

      <div className={s.card}>
        <div className={s.cardTitle}>Overview</div>
        <p className={s.text}>
          Chameleon Table is played by 2 to 5 players who draw cards from a shared supply
          and build up collections of colors in their play area. At the end of the game,
          each player counts their cards by color, but only the 3 largest color groups
          score positive points — every other color counts against them. The more cards
          you hold in one of your best colors, the more points it's worth. Whoever has
          the highest score when the match ends wins.
        </p>
      </div>

      <div className={s.card}>
        <div className={s.cardTitle}>Setup</div>
        <p className={s.text}>
          When a room starts, the table is set automatically: one row is placed for each
          player in the game, the deck is shuffled, and a "last round" card is hidden
          somewhere inside it so nobody knows exactly when the final round will begin.
          Turn order is decided by the order players joined the room.
        </p>
      </div>

      <div className={s.card}>
        <div className={s.cardTitle}>On your turn</div>
        <p className={s.text}>
          On your turn you must choose one of two actions, then play passes to the next
          player.
        </p>
        <p className={s.text}>
          <strong>Draw and place a card</strong> — draw the top card from the supply and
          place it face up next to any row. A row can never hold more than 3 cards; once
          it does, no one may add to it. If every row is full, this action is no longer
          available and you must take a row instead.
        </p>
        <p className={s.text}>
          <strong>Take a row</strong> — claim any row that has at least one card next to
          it, along with all its cards, and add them to your play area, sorted by color.
          If you take a joker, set it aside — you'll assign it to a color only at the end
          of the game. Once you've taken a row, you're done for the round: you take no
          further turns until the next one begins.
        </p>
        <p className={s.text}>
          A round ends once every player has taken a row. Rows are cleared, and a new
          round starts with whoever took the last row of the previous one.
        </p>
      </div>

      <div className={s.card}>
        <div className={s.cardTitle}>Scoring</div>
        <p className={s.text}>
          When the "last round" card is drawn, the current round becomes the final one.
          Once it ends, each player assigns their jokers to a color of their choice and
          counts their cards in every color they hold. Only the 3 best colors count as
          positive points for each player — every other color counts against them, using
          the same table:
        </p>
        <table className={s.scoreTable}>
          <thead>
            <tr>
              <th>Cards in a color</th>
              <th>Points</th>
            </tr>
          </thead>
          <tbody>
            {SCORE_TABLE.map((row) => (
              <tr key={row.cards}>
                <td>{row.cards}</td>
                <td>{row.points}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className={s.text}>
          Each "+2" card in your play area is worth 2 extra points, no matter its color.
          Add up your 3 best colors, subtract the rest, add your "+2" bonuses — that's
          your final score.
        </p>
      </div>

      <div className={s.card}>
        <div className={s.cardTitle}>Staying in the game</div>
        <p className={s.text}>
          Each turn has a time limit — if you don't act in time, you're marked inactive
          and your seat is skipped so the game can keep moving. A match can continue with
          as few as 2 active players; if it ever drops below that, the match ends early
          and no winner is declared. If your connection drops, you can rejoin from the
          lobby as long as the room is still open.
        </p>
        <p className={s.text}>
          If a player leaves or is disconnected mid-round, the number of rows on the
          table doesn't change right away — it stays as it was for the rest of that
          round. The board adjusts to match the new player count starting with the
          next round.
        </p>
      </div>

    </div>
  )
}

export default Rules
