from collections import Counter, OrderedDict
from itertools import combinations
from ai_environment import AIEnvironment 
from ai_environment import BetterEnum
from typing import List, Tuple
from enum import Enum

from math import inf
from pokerkit import NoLimitTexasHoldem, Automation, Mode

#The exact numers don't matter extactly just need gaps between them to calculate score

# class PokerHand(Enum):
#     HIGHCARD = 1
#     PAIR = 15
#     TWOPAIR = 30 #has to be handles slightly different becasue of the kicker
#     THREEOFAKIND = 44
#     STRAIGHT = 58
#     FLUSH = 70
#     FULLHOUSE = 84
#     FOUROFAKIND = 100
#     STRAIGHTFLUSH = 110
#     ROYALFLUSH = 115

# class Card:
#     def __init__(self, suit: int, rank: int):
#         self.suit = suit
#         self.rank = rank
# class Board:
#     def get_hand_rank(self, hand: List[Card]) -> Tuple[int, List[int]]:
#         """Evaluates the best poker hand ranking and returns a tuple (rank index, tiebreaker list)."""
#         ranks = [card.rank for card in hand]
#         suits = [card.suit for card in hand]
#         rank_counts = {r: ranks.count(r) for r in set(ranks)}
        
#         # Sorted ranks for tie-breakers
#         sorted_ranks = sorted(ranks, reverse=True)

#         is_flush = len(set(suits)) == 1
#         is_straight = len(set(ranks)) == 5 and (sorted_ranks[0] - sorted_ranks[-1] == 4)

#         if is_straight and is_flush:
#             return (9 if sorted_ranks[0] == "A" else 8, [sorted_ranks[0]])  # Royal/Straight Flush

#         # Four of a kind
#         if 4 in rank_counts.values():
#             four_rank = max(rank_counts, key=lambda r: rank_counts[r] == 4)
#             kicker = max([r for r in ranks if r != four_rank])
#             return (7, [four_rank, kicker])

#         # Full house
#         if sorted(rank_counts.values()) == [2, 3]:
#             triple = max(rank_counts, key=lambda r: rank_counts[r] == 3)
#             pair = max(rank_counts, key=lambda r: rank_counts[r] == 2)
#             return (6, [triple, pair])

#         # Flush
#         if is_flush:
#             return (5, sorted([r for r in ranks], reverse=True))

#         # Straight
#         if is_straight:
#             return (4, [sorted_ranks[0]])

#         # Three of a kind
#         if 3 in rank_counts.values():
#             triple = max(rank_counts, key=lambda r: rank_counts[r] == 3)
#             kickers = sorted([r for r in ranks if r != triple], reverse=True)
#             return (3, [triple] + kickers)

#         # Two Pair
#         pairs = [r for r in rank_counts if rank_counts[r] == 2]
#         if len(pairs) == 2:
#             high_pair, low_pair = sorted(pairs, reverse=True)
#             kicker = max([r for r in ranks if r not in pairs])
#             return (2, [high_pair, low_pair, kicker])

#         # One Pair
#         if 2 in rank_counts.values():
#             pair = max(rank_counts, key=lambda r: rank_counts[r] == 2)
#             kickers = sorted([r for r in ranks if r != pair], reverse=True)
#             return (1, [pair] + kickers)

#         # High Card
#         return (0, sorted([r for r in ranks], reverse=True))

#     def best_hand(self, board: List[Card], player_hand: List[Card]) -> Tuple[int, List[int]]:
#         """Finds the best possible 5-card hand from the given board and player's hole cards."""
#         all_cards = board + player_hand
#         return max((self.get_hand_rank(list(combo)) for combo in combinations(all_cards, 5)), key=lambda x: x)

#     def compare_hands(self, board: List[Card], hand1: List[Card], hand2: List[Card]) -> str:
#         """Compares two poker hands and determines the winner."""
#         rank1, tiebreaker1 = self.best_hand(board, hand1)
#         rank2, tiebreaker2 = self.best_hand(board, hand2)

#         if rank1 > rank2:
#             return "Player 1 wins"
#         elif rank2 > rank1:
#             return "Player 2 wins"
#         else:
#             return "Tie" if tiebreaker1 == tiebreaker2 else ("Player 1 wins" if tiebreaker1 > tiebreaker2 else "Player 2 wins")

        



class PokerEnvironment:
    def __init__(self, player_count=2, small_blind=50, big_blind=100, stacks=None):
        if stacks is None:
            stacks = [20000] * player_count
        self.game = NoLimitTexasHoldem.create_state(
            (
                Automation(Automation.ANTE_POSTING),
                Automation(Automation.BET_COLLECTION),
                Automation(Automation.BLIND_OR_STRADDLE_POSTING),
                Automation(Automation.HOLE_CARDS_SHOWING_OR_MUCKING),
                Automation(Automation.HAND_KILLING),
                Automation(Automation.CHIPS_PUSHING),
                Automation(Automation.CHIPS_PULLING),
            ),
            False,
            {-1: 600},
            (200, 400, 800),
            400,
            tuple(stacks),
            len(stacks),
            mode=Mode.CASH_GAME,
        )
        self.currentIndex = 0 
        self.game_agent_count = 0
        self.registered_agents = 0
        self.currentGame: List[str] = []
    
    
    def load_specific_game(self, whole_game: List[str], stacks: List[int], agent_count:int=0):
        """
         Load a game with specific format
         
         First line is the game settings / formant
         Args
            whole_game: The whole game, for the agent injection specify their spot with A1, A2 etc. 
            agent_count: Amount of agents needed for the game
         """
        game_settings = whole_game[0].split(' ')
        self.game = NoLimitTexasHoldem.create_state(
            automations=(
                Automation(Automation.ANTE_POSTING),
                Automation(Automation.BET_COLLECTION),
                Automation(Automation.BLIND_OR_STRADDLE_POSTING),
                Automation(Automation.HOLE_CARDS_SHOWING_OR_MUCKING),
                Automation(Automation.HAND_KILLING),
                Automation(Automation.CHIPS_PUSHING),
                Automation(Automation.CHIPS_PULLING),
            ),
            ante_trimming_status=game_settings[0] == 'True',  # Uniform antes?
            raw_antes={-1: int(game_settings[1])},  # Antes
            raw_blinds_or_straddles=(int(game_settings[2]), int(game_settings[3]), int(game_settings[4])),  # Blinds or straddles
            min_bet=int(game_settings[5]),  # Min-bet
            raw_starting_stacks=tuple(stacks),
            player_count=len(stacks),  # Number of players
            mode=Mode.TOURNAMENT,
        )
        self.currentGame = whole_game
        self.currentIndex = 1
        self.game_agent_count = agent_count
        if(self.registered_agents != self.game_agent_count):
            raise Exception("Did not register enough agents")
        
    def register_agent(self) -> int:
        """
         Register an agent and issue them an ID
         
         If too many agents for a game will raise an exception and won't run
        """
        
        if(self.registered_agents == self.game_agent_count):
            raise ValueError("Too many agents for the game")
        self.registered_agents += 1
        return self.registered_agents
    
    def clear_agents(self):
        self.registered_agents = 0
    def update_state(self):
        self.state = {
            "board": self.game.get_board_cards(0),
            "main_pot": list(self.game.pots)[0],
            "side_pot": list(self.game.pots)[1:],
            "actions": [action.name for action in self.game.actions],
            "raises": [a for a in self.game.round.actions if a.name == 'RAISE'],
            "calls": [a for a in self.game.round.actions if a.name == 'CALL'],
            "folds": [a for a in self.game.round.actions if a.name == 'FOLD'],
            "checks": [a for a in self.game.round.actions if a.name == 'CHECK'],
            "current_player": self.game.actor.index,
            "legal_actions": [a.name for a in self.game.legal_actions]
        }

    def get_state(self):
        return self.state

    def make_move(self, player_id: int, action, amount=None) -> str:
        if player_id != self.game.actor_index:
            return "Out of Turn"

        action = action.lower()
        #have to figure out the legal actions
        legal = [a.name.lower() for a in self.game.legal_actions]
        if action not in legal:
            return "Illegal Action"

        if action == 'fold':
            self.game.fold()
        elif action == 'call' or action == 'check':
            self.game.check_or_call()
        elif action == 'raise':
            if amount is None:
                return "Raise amount needed"
            self.game.complete_bet_or_raise_to(amount)
        else:
            return "Unsupported action"

        self.update_state()
        return "Action Made"

    def is_terminal(self):
        return not self.game.status
    
     


# class Player:
#    pass 
   

    
    
            
        
# class PokerState():
#     def __init__(self, board = [], pot  = 0):
#         self.board = board
#         self.pot = pot
    
# class PokerEnvironment(AIEnvironment[PokerState, BetterEnum, BetterEnum]):
#     #def __init__(self):
#     pass    
    