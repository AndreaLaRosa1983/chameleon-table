import random
from backend.game import assign_initial_colors, create_deck, create_players
from backend.models import CardType


def test_assigned_colors_present_in_deck_two_players():
    """Ogni colore assegnato ai giocatori deve comparire nel mazzo.
    Regression: assign_initial_colors ritornava colors[:n], scartando
    i colori del secondo giocatore, che create_deck poteva rimuovere."""
    for _ in range(100):
        players = create_players(["Anna", "Bruno"])
        returned = assign_initial_colors(players)          
        deck = create_deck(len(players), returned)

        assigned = {c.color for p in players for c in p.cards if c.card_type == CardType.COLOR}
        in_deck = {c.color for c in deck if c.card_type == CardType.COLOR}

        assert assigned <= in_deck, f"Colori assegnati mancanti dal mazzo: {assigned - in_deck}"