import s from './CardCarousel.module.scss'

const CARD_IMAGES = [
  '/assets/green.png',
  '/assets/blue.png',
  '/assets/red.png',
  '/assets/yellow.png',
  '/assets/brown.png',
  '/assets/purple.png',
  '/assets/orange.png',
  '/assets/cotton.png',
]

function CardCarousel() {
  const count = CARD_IMAGES.length
  const angleStep = 360 / count
  // NB!!! Radius tuned for 8 cards at current width — cards overlap if count grows.
  const RADIUS = 280
  return (
    <div className={s.carouselWrapper}>
      <div className={s.scene}>
        <div className={s.carousel}>
          {CARD_IMAGES.map((src, i) => (
            <div
              key={src}
              className={s.cardSlot}
              style={{
                transform: `rotateY(${angleStep * i}deg) translateZ(${RADIUS}px)`,
              }}
            >
              <img src={src} alt="" className={s.cardImg} />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default CardCarousel