

from backend.models import CardType, CardColor, Player, GameState, GamePhase, Row, Card

def make_state(player_configs: list[dict]) -> GameState:
    # Helper: creates minimal GameState with players and turn_order
    players = []
    for cfg in player_configs:
        p = Player(name=cfg["name"])
        p.passed = cfg.get("passed", False)
        p.active = cfg.get("active", True)
        players.append(p)

    return GameState(
        room_code="TEST",
        players=players,
        turn_order=[cfg["name"] for cfg in player_configs]
    )

def make_game_state_for_take_row() -> GameState:
    # Helper: creates a GameState ready for take_row tests.
    players = [
        Player(name="Alice"),
        Player(name="Bob"),
        Player(name="Charlie"),
    ]
    rows = [
        Row(cards=[Card(card_type=CardType.COLOR, color=CardColor.RED)]),
        Row(cards=[Card(card_type=CardType.COLOR, color=CardColor.BLUE)]),
        Row(cards=[Card(card_type=CardType.COLOR, color=CardColor.GREEN)]),
    ]
    return GameState(
        room_code="TEST",
        players=players,
        rows=rows,
        turn_order=["Alice", "Bob", "Charlie"],
        round_starter="Alice"
    )
     
def make_game_state_for_end_round(last_round: bool = False) -> GameState:
    """Helper: creates a GameState where all players have passed."""
    players = [
        Player(name="Alice", passed=True),
        Player(name="Bob", passed=True),
        Player(name="Charlie", passed=True),
    ]
    rows = [
        Row(cards=[], taken_by="Bob"),
        Row(cards=[], taken_by="Alice"),
        Row(cards=[], taken_by="Charlie"),
    ]
    return GameState(
        room_code="TEST",
        players=players,
        rows=rows,
        turn_order=["Alice", "Bob", "Charlie"],
        round_starter="Alice",
        last_row_taker="Charlie",
        last_round=last_round,
        phase=GamePhase.PLAYING
    )
    
def make_game_state_for_draw_card() -> GameState:
    #Helper: creates a GameState ready for draw_card tests.
    players = [
        Player(name="Alice"),
        Player(name="Bob"),
        Player(name="Charlie"),
    ]
    rows = [
        Row(cards=[]),
        Row(cards=[]),
        Row(cards=[]),
    ]
    deck = [
        Card(card_type=CardType.COLOR, color=CardColor.RED),
        Card(card_type=CardType.COLOR, color=CardColor.BLUE),
        Card(card_type=CardType.COLOR, color=CardColor.GREEN),
    ]
    return GameState(
        room_code="TEST",
        players=players,
        rows=rows,
        deck=deck,
        turn_order=["Alice", "Bob", "Charlie"],
        round_starter="Alice",
        phase=GamePhase.PLAYING
    )

def make_game_state_for_place_card() -> GameState:
    #Helper: creates a GameState ready for place_card tests.
    players = [
        Player(name="Alice"),
        Player(name="Bob"),
        Player(name="Charlie"),
    ]
    rows = [
        Row(cards=[]),
        Row(cards=[]),
        Row(cards=[]),
    ]
    return GameState(
        room_code="TEST",
        players=players,
        rows=rows,
        deck=[],
        turn_order=["Alice", "Bob", "Charlie"],
        round_starter="Alice",
        phase=GamePhase.PLAYING
    )

def make_players_for_calculate_score() -> list[Player]:
    #Helper: creates 3 players with realistic card distributions.
    
    def make_color_cards(color: CardColor, count: int) -> list[Card]:
        return [Card(card_type=CardType.COLOR, color=color) for _ in range(count)]
    
    def make_plus2_cards(count: int) -> list[Card]:
        return [Card(card_type=CardType.PLUS2) for _ in range(count)]
    
    def make_joker_cards(count: int) -> list[Card]:
        return [Card(card_type=CardType.JOKER) for _ in range(count)]
    
    alice = Player(name="Alice")
    alice.cards = (
        make_color_cards(CardColor.BLUE, 5) +
        make_color_cards(CardColor.GREEN, 4) +
        make_color_cards(CardColor.RED, 3) +
        make_color_cards(CardColor.YELLOW, 1) +
        make_color_cards(CardColor.PURPLE, 1) +
        make_color_cards(CardColor.ORANGE, 1) +
        make_plus2_cards(3)
    )

    bob = Player(name="Bob")
    bob.cards = (
        make_color_cards(CardColor.YELLOW, 4) +
        make_color_cards(CardColor.RED, 3) +
        make_color_cards(CardColor.ORANGE, 3) +
        make_color_cards(CardColor.BLUE, 1) +
        make_color_cards(CardColor.GREEN, 1) +
        make_color_cards(CardColor.PURPLE, 2) +
        make_plus2_cards(3)
    )
    bob.jokers = make_joker_cards(1)

    charlie = Player(name="Charlie")
    charlie.cards = (
        make_color_cards(CardColor.PURPLE, 4) +
        make_color_cards(CardColor.GREEN, 3) +
        make_color_cards(CardColor.ORANGE, 3) +
        make_color_cards(CardColor.RED, 2) +
        make_color_cards(CardColor.BLUE, 1) +
        make_color_cards(CardColor.YELLOW, 1) +
        make_plus2_cards(3)
    )
    charlie.jokers = make_joker_cards(2)
    
    return [alice, bob, charlie]