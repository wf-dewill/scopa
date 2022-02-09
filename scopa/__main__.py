import random
import os
from typing import List, Dict, Tuple, Callable

import pygame

# Margins
MARGIN_LEFT = 230
MARGIN_TOP = 150

# WINDOW SIZE
# WIDTH = 1600
# HEIGHT = 1000
WIDTH = 1680
HEIGHT = 1050


# Card sizes
CARD_WIDTH = 100
CARD_HEIGHT = 160

# Hand placements
LOWER_HAND_HEIGHT = 5*HEIGHT/6
UPPER_HAND_HEIGHT = HEIGHT/6
HAND_LEFT_3 = 5*WIDTH/12
HAND_RIGHT_3 = 7*WIDTH/12
HAND_MIDDLE = WIDTH/2
HAND_LEFT_2 = 11*WIDTH/24
HAND_RIGHT_2 = 13*WIDTH/24
CENTRE_HAND_HEIGHT = HEIGHT/2
CENTRE_HAND_RIGHT_MARGIN = WIDTH - CARD_WIDTH*1.5
DECK_y = HEIGHT/2
DECK_x = CARD_WIDTH*1.1
UPPER_WON_HEIGHT = HEIGHT/3 - CARD_HEIGHT
WON_WIDTH = CENTRE_HAND_RIGHT_MARGIN
LOWER_WON_HEIGHT = 2*HEIGHT/3 + CARD_HEIGHT

CENTRE_UPPER_BOUND = HEIGHT/3 - CARD_HEIGHT/2
CENTRE_LOWER_BOUND = 2*HEIGHT/3 + CARD_HEIGHT/2

# Button Constants
BUTTON_WIDTH = 3*CARD_WIDTH
BUTTON_HEIGHT = CARD_HEIGHT/2



# COLORS
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (110, 110, 110)
GREEN = (0, 255, 0)
LIGHT_GREEN = (0, 120, 0)
RED = (255, 0, 0)
LIGHT_RED = (120, 0, 0)

fileloc = os.path.dirname(__file__)

IMAGE_PATH = os.path.join(fileloc, "resources/images/")
BACK_IMAGE_PATH = os.path.join(fileloc, "resources/images/Dummy/Dummy_Dummy.jpg")
ICON_PATH = os.path.join(fileloc, "resources/italy.png")

SUITS = ("Coins", "Clubs", "Cups", "Swords",)
VALUES = range(1, 11)

START_DECK_VALUES = [
    (suit, value)
    for suit in SUITS
    for value in VALUES
]

DEAL_INTERVAL = 30
MOVE_INTERVAL = 60

PLACEMENT_DICT = {
    0: HAND_RIGHT_3,
    1: HAND_MIDDLE,
    2: HAND_LEFT_3,
}

NAPOLA_CARDS = [(1, "Coins"), (2, "Coins"), (3, "Coins")]

FPS = 60

FAKE_VALUES = [
    ("Coins", 2),
    ("Coins", 3),
    ("Clubs", 2),
    ("Clubs", 3),
    ("Cups", 2),
    ("Cups", 3),
    ("Swords", 2),
    ("Swords", 3),
    ("Coins", 1),
    ("Clubs", 1),
    ("Cups", 1),
    ("Swords", 1),
]


class Card(pygame.sprite.Sprite):
    def __init__(self, suit, value, position):
        super().__init__()
        self.suit = suit
        self.value = value
        self.position = position
        self._image = pygame.image.load(os.path.join(IMAGE_PATH, f"{self.suit}/{self.value}_{self.suit}.jpg")).convert()
        self._base_image = pygame.transform.scale(self._image, (CARD_WIDTH, CARD_HEIGHT))
        self._back_image = pygame.image.load(BACK_IMAGE_PATH).convert()
        self._base_back_image = pygame.transform.scale(self._back_image, (CARD_WIDTH, CARD_HEIGHT))
        self.image = self._base_image.copy()
        self.back_image = self._base_back_image.copy()
        self.rect = self.image.get_rect()
        self.rect.center = position
        self.offset_x = 0
        self.offset_y = 0
        self.initial_x = self.rect.centerx
        self.initial_y = self.rect.centery
        self.dragging = False
        self.showing = True

    def __repr__(self) -> str:
        return f"{self.value} of {self.suit}"

    def __eq__(self, other) -> bool:
        return self.suit == other.suit and self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value) * hash(self.suit)

    def string(self) -> str:
        return self.__repr__()

    def tuple(self) -> Tuple[int, str]:
        return self.value, self.suit

    def draw(self, screen: pygame.Surface, x, y):
        screen.blit(self.image, (x, y))

    def set_position(self, x, y):
        self.rect.center = (x, y)
        if not self.dragging:
            self.initial_x = x
            self.initial_y = y

    def flip(self):
        if self.showing:
            self.image = self.back_image.copy()
            self.showing = False
        else:
            self.image = self._base_image.copy()
            self.showing = True


class Controller:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.deck_values = random.sample(START_DECK_VALUES, 40)

        # These lists hold the cards for each object player.
        self.lower_cards: List[Card] = list()
        self.upper_cards: List[Card] = list()
        self.centre_cards: List[Card] = list()
        self.lower_won_cards: List[Card] = list()
        self.upper_won_cards: List[Card] = list()
        self.holder: List[Card] = list()

        # These this ares for the computer
        self.chosen_card: Card = None
        self.chosen_option: List[Card] = None
        self.centre_updated = False

        # List of buttons if buttons are present, used for drawing.
        self.buttons: List[OptionButton] = list()

        # Used for animating the cards as part of draw loop.
        # Of the form: Card, placement, incrementx, incrementy .
        # Will increment the position of the card each frame.
        self.dealables: List[(Card, str, int, int)] = list()
        self.moveables: List[(Card, str, int, int)] = list()

        # Cannot set defaults for these, needs screen to be created first.
        self.deck_card = Card("Dummy", "Dummy", (DECK_x, DECK_y))
        self.upper_won_card = Card("Dummy", "Dummy", (WON_WIDTH, UPPER_WON_HEIGHT))
        self.lower_won_card = Card("Dummy", "Dummy", (WON_WIDTH, LOWER_WON_HEIGHT))

        self.pointer = 0
        self.player_1_turn = True
        self.player_last_won = False
        self.lower_points = 0
        self.upper_points = 0
        self.dealing = True
        self.first_deal = True
        self.wait_for_button = False
        self.empty = False
        self.game_running = True
        self.restart = False
        self.quit = False


class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, text: str, w=BUTTON_WIDTH, h=BUTTON_HEIGHT):
        super().__init__()
        self.font = pygame.font.SysFont(None, 25)
        self.text = text
        text_surf = self.font.render(self.text, True, WHITE)
        self.button_image = pygame.Surface((w, h))
        self.button_image.fill(BLACK)
        self.button_image.blit(text_surf, text_surf.get_rect(center=(w // 2, h // 2)))
        self.hover_image = pygame.Surface((w, h))
        self.hover_image.fill(GRAY)
        self.hover_image.blit(text_surf, text_surf.get_rect(center=(w // 2, h // 2)))
        pygame.draw.rect(self.hover_image, (96, 196, 96), self.hover_image.get_rect(), 3)
        self.image = self.button_image
        self.rect = pygame.Rect(x, y, w, h)

    def set_position(self, x, y):
        self.rect.center = (x, y)

    def draw(self, screen):
        screen.blit(self.image, (self.rect.x, self.rect.y))


class OptionButton(Button):
    def __init__(self, x, y, initial_card: Card, option: List[Card], scopa: bool = False):
        self.initial_card = initial_card
        self.option = option
        self.text = ', '.join([card.string() for card in self.option])
        self.scopa = scopa
        super().__init__(x, y, text=self.text)



def _build():
    # Setting up caption
    pygame.display.set_caption("Scopa")

    # Loading image for the icon
    icon = pygame.image.load(ICON_PATH)

    # Setting the game icon
    pygame.display.set_icon(icon)


def get_board() -> pygame.Surface:
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    screen.fill(GREEN)
    return screen


def draw_hand(hand: List[Card], screen: pygame.Surface) -> None:
    for card in hand:
        card.draw(screen, card.rect.x, card.rect.y)


def draw_hands(controller: Controller) -> None:
    dealing_hand = list()
    moving_hand = list()
    holder_hand = [card for card in controller.holder]
    if controller.moveables:
        moving_hand = [moveable[0] for moveable in controller.moveables]
    elif controller.dealables:
        dealing_card, _, _, _ = controller.dealables[0]
        dealing_hand = [dealing_card]
    for hand in (controller.lower_cards, controller.upper_cards, controller.centre_cards, dealing_hand, moving_hand, holder_hand):
        draw_hand(hand, controller.screen)


def draw_buttons(controller: Controller) -> None:
    for button in controller.buttons:
        button.draw(controller.screen)


def draw_controller(controller: Controller) -> None:
    controller.screen.fill(GREEN)
    draw_hands(controller)
    if len(controller.deck_values) != 0:
        draw_hand([controller.deck_card], controller.screen)
    if len(controller.buttons) != 0:
        draw_buttons(controller)
    if len(controller.upper_won_cards) != 0:
        draw_hand([controller.upper_won_card], controller.screen)
    if len(controller.lower_won_cards) != 0:
        draw_hand([controller.lower_won_card], controller.screen)
    pygame.draw.line(controller.screen, BLACK, (0, CENTRE_LOWER_BOUND), (WIDTH, CENTRE_LOWER_BOUND))
    pygame.draw.line(controller.screen, BLACK, (0, CENTRE_UPPER_BOUND), (WIDTH, CENTRE_UPPER_BOUND))
    pygame.display.flip()


def deal_cards(controller: Controller, centre_deal: bool = False) -> Controller:
    initial_lower = controller.lower_cards
    initial_upper = controller.upper_cards
    if controller.dealables:
        if controller.pointer != DEAL_INTERVAL:
            card, placement, incrementx, incrementy = controller.dealables[0]
            card.set_position(card.initial_x+incrementx, card.initial_y+incrementy)
            controller.pointer = controller.pointer + 1
        else:
            card, placement, _, _ = controller.dealables[0]
            if placement == "lower":
                controller.lower_cards = controller.lower_cards + [card]
            elif placement == "upper":
                controller.upper_cards = controller.upper_cards + [card]
            else:
                controller.centre_cards = controller.centre_cards + [card]
                controller = rearrange_centre_cards(controller)
            controller.dealables = list()
            controller.pointer = 0

    else:
        if centre_deal:
            suit, value = controller.deck_values.pop()
            card = Card(suit, value, (DECK_x, DECK_y))
            endy = CENTRE_HAND_HEIGHT
            endx = WIDTH/2
            incrementx = (endx - card.initial_x) / DEAL_INTERVAL
            incrementy = (endy - card.initial_y) / DEAL_INTERVAL
            controller.dealables = controller.dealables + [(card, "centre", incrementx, incrementy)]
        else:
            if len(initial_lower) <= len(initial_upper):
                suit, value = controller.deck_values.pop()
                card = Card(suit, value, (DECK_x, DECK_y))
                endy = LOWER_HAND_HEIGHT
                endx = PLACEMENT_DICT[len(initial_lower)]
                incrementx = (endx - card.initial_x) / DEAL_INTERVAL
                incrementy = (endy - card.initial_y) / DEAL_INTERVAL
                controller.dealables = controller.dealables + [(card, "lower", incrementx, incrementy)]
            else:
                suit, value = controller.deck_values.pop()
                card = Card(suit, value, (DECK_x, DECK_y))
                card.flip()
                endy = UPPER_HAND_HEIGHT
                endx = PLACEMENT_DICT[len(initial_upper)]
                incrementx = (endx - card.initial_x) / DEAL_INTERVAL
                incrementy = (endy - card.initial_y) / DEAL_INTERVAL
                controller.dealables = controller.dealables + [(card, "upper", incrementx, incrementy)]
    return controller


def rearrange_buttons(controller: Controller) -> Controller:
    increment = BUTTON_HEIGHT * 1.1
    pixels_needed = len(controller.buttons) * increment
    bottom_margin = HEIGHT/2 - pixels_needed/2

    for i, button in enumerate(controller.buttons):
        button.set_position(WIDTH/2, i * increment + bottom_margin)
    return controller


def rearrange_centre_cards(controller: Controller) -> Controller:
    increment = CARD_WIDTH*1.5
    pixels_needed = len(controller.centre_cards)*increment

    left_margin = 7*WIDTH/12 - pixels_needed/2

    for i, card in enumerate(controller.centre_cards):
        card.set_position(i*increment+left_margin, CENTRE_HAND_HEIGHT)
    return controller


def move_cards(controller: Controller, cards: List[Card], centre: bool = False, place: str = "") -> Controller:
    if controller.moveables:
        if controller.pointer != MOVE_INTERVAL:
            for moveable in controller.moveables:
                card, placement, incrementx, incrementy = moveable
                card.set_position(card.initial_x+incrementx, card.initial_y+incrementy)
            controller.pointer = controller.pointer + 1
        else:
            for moveable in controller.moveables:
                card, placement, _, _ = moveable
                if placement == "centre":
                    controller.centre_cards = controller.centre_cards + [card]
                    controller.centre_updated = True
                elif placement == "upper_won":
                    controller.upper_won_cards = controller.upper_won_cards + [card]
                    controller.player_last_won = False
                else:
                    controller.lower_won_cards = controller.lower_won_cards + [card]
                    controller.player_last_won = True
            controller.moveables = list()
            controller.pointer = 0
            if not controller.centre_updated:
                controller.player_1_turn = not controller.player_1_turn
            return rearrange_centre_cards(controller)
    elif controller.player_1_turn or place == "lower":
        endy = LOWER_WON_HEIGHT
        endx = WON_WIDTH
        for card in cards:
            if card in controller.holder:
                controller.holder.remove(card)
            incrementx = (endx - card.initial_x) / MOVE_INTERVAL
            incrementy = (endy - card.initial_y) / MOVE_INTERVAL
            controller.moveables = controller.moveables + [(card, "lower_won", incrementx, incrementy)]
    elif centre:
        endy = CENTRE_HAND_HEIGHT
        endx = WIDTH / 2
        for card in cards:
            if card in controller.holder:
                controller.holder.remove(card)
            incrementx = (endx - card.initial_x) / MOVE_INTERVAL
            incrementy = (endy - card.initial_y) / MOVE_INTERVAL
            controller.moveables = controller.moveables + [(card, "centre", incrementx, incrementy)]
    else:
        endy = UPPER_WON_HEIGHT
        endx = WON_WIDTH
        for card in cards:
            if card in controller.holder:
                controller.holder.remove(card)
            incrementx = (endx - card.initial_x) / MOVE_INTERVAL
            incrementy = (endy - card.initial_y) / MOVE_INTERVAL
            controller.moveables = controller.moveables + [(card, "upper_won", incrementx, incrementy)]
    return controller


def valid_options(options: List[List[Card]]):
    if options:
        if any(len(option) == 1 for option in options):
            return [option for option in options if len(option) == 1]
    return options


def calculate_options(card: Card, centre_cards: List[Card]):
    def summation(centre: List[Card], total: int):
        def func(cards: List[Card], total_num: int, partial=list(), partial_sum=0):
            if partial_sum == total_num:
                yield partial
            if partial_sum >= total_num:
                return
            for i, card in enumerate(cards):
                remaining = cards[i + 1:]
                yield from func(remaining, total_num, partial + [card], partial_sum + card.value)
        return func(centre, total)

    return valid_options(list(summation(centre_cards, card.value)))


def turn_logic(card: Card, controller: Controller,) -> Controller:

    if controller.player_1_turn:
        controller.lower_cards.remove(card)
        controller.holder = controller.holder + [card]
        win_options = calculate_options(card, controller.centre_cards)
        if win_options:

            controller.buttons = controller.buttons + [
                OptionButton(x=WIDTH, y=HEIGHT/2, initial_card=card, option=option, scopa=(len(option) == len(controller.centre_cards)))
                for option in win_options
            ]
            controller = rearrange_buttons(controller)
            controller.wait_for_button = True
        else:
            controller.centre_cards = controller.centre_cards + [card]

    return rearrange_centre_cards(controller)


def event_loop(event, hand: List[Card], controller: Controller):
    if event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1:
            for card in hand:
                if card.rect.collidepoint(event.pos):
                    card.initial_x = card.rect.centerx
                    card.initial_y = card.rect.centery
                    card.dragging = True
                    mouse_x, mouse_y = event.pos
                    card.offset_x = card.rect.centerx - mouse_x
                    card.offset_y = card.rect.centery - mouse_y

    elif event.type == pygame.MOUSEBUTTONUP:
        for card in hand:
            if event.button == 1:
                x, y = event.pos
                if CENTRE_UPPER_BOUND <= y + card.offset_y <= CENTRE_LOWER_BOUND and card.dragging:
                    card.set_position(x + card.offset_x, y + card.offset_y)
                    card.dragging = False
                    controller = turn_logic(card, controller,)
                    if controller.wait_for_button:
                        return controller
                    if not controller.moveables:
                        controller.player_1_turn = not controller.player_1_turn
                    return rearrange_centre_cards(controller)
                elif card.dragging:
                    card.set_position(card.initial_x, card.initial_y)
                    card.dragging = False
                card.dragging = False

    elif event.type == pygame.MOUSEMOTION:
        for card in hand:
            if card.dragging:
                x, y = event.pos
                card.set_position(x + card.offset_x, y + card.offset_y)
    return controller


def combine_priorities(*ints) -> int:
    return sum(ints)


def option_weight(card: Card, option: List[Card], controller: Controller, combiner: Callable = combine_priorities):

    won_cards = controller.upper_won_cards
    lost_cards = controller.lower_won_cards
    winnable_cards = option + [card]

    won_tuples = [card.tuple() for card in won_cards]
    lost_tuples = [card.tuple() for card in lost_cards]
    winnable_tuples = [card.tuple() for card in winnable_cards]

    won_golds = len([card for card in won_cards if card.suit == "Coins"])
    lost_golds = len([card for card in lost_cards if card.suit == "Coins"])
    winnable_golds = [card for card in winnable_cards if card.suit == "Coins"]

    won_napola_cards = len([card for card in NAPOLA_CARDS if card in won_tuples])
    lost_napola_cards = len([card for card in NAPOLA_CARDS if card in lost_tuples])
    winnable_napola_cards = len([card for card in NAPOLA_CARDS if card in winnable_tuples])

    won_sevens = len([card for card in won_cards if card.value == 7])
    lost_sevens = len([card for card in lost_cards if card.value == 7])
    winnable_sevens = len([card for card in winnable_cards if card.value == 7])

    napola_priority = 0
    seven_priority = 0
    gold_seven_priority = 0
    golds_priority = 0
    cards_priority = len(winnable_cards)
    scopa_priority = 10 if len(controller.centre_cards) == len(winnable_cards) else 0

    # TODO: Rewrite napola choosing
    if winnable_napola_cards:
        if lost_napola_cards == 3:
            # Lost napola point, Just stop them getting more golds
            if winnable_golds:
                napola_priority = min(winnable_golds, key=lambda c: c.value)
        else:
            if winnable_napola_cards >= 1:
                if lost_napola_cards >= 1:
                    # Stop other player getting napola
                    napola_priority = (lost_napola_cards + winnable_napola_cards)*2
                else:
                    # Can take it easy
                    napola_priority = winnable_napola_cards
            if won_napola_cards >= 1:
                # More incentive to get the napola cards
                napola_priority = napola_priority * (won_napola_cards + 1)
            if won_napola_cards == 3:
                if winnable_golds:
                    # Grab as many cards as we can get
                    napola_priority = napola_priority * 3

    if (7, "Coins") in winnable_tuples:
        gold_seven_priority = 10

    if winnable_sevens:
        if lost_sevens > 2:
            # Lost the seven point
            pass
        elif lost_sevens == 2:
            # Stop them getting more sevens
            seven_priority = winnable_sevens * 2
        else:
            # Lost sevens is either 0 or 1 so still have a chance
            if won_sevens >= 2:
                # Already won the point, no need to prioritze
                seven_priority = winnable_sevens
            else:
                # Won sevens is 0 or 1 so can still win
                seven_priority = winnable_sevens * 3

    if winnable_golds:
        if lost_golds > 5:
            # Lost point
            pass
        elif lost_golds == 5:
                # Stop them getting more golds
                golds_priority = len(winnable_golds) * 2
        else:
            # Lost golds is less than 5 so can still win point
            if won_golds >= 5:
                # Already won, no need to prioritize
                golds_priority = len(winnable_golds)
            else:
                # Won golds is 4 or below so can still win
                golds_priority = len(winnable_golds) * 3

    return combiner(napola_priority, seven_priority, gold_seven_priority, golds_priority, cards_priority, scopa_priority)


def decide_option(controller: Controller) -> Tuple[Card, List[Card]]:
    hand = controller.upper_cards
    options_dict = {card: calculate_options(card, controller.centre_cards) for card in hand}
    options_weight_dict = {
        card: {
            option_weight(card, option, controller): option
            for option in options_dict[card]
        }
        for card in options_dict
    }
    tupled = [(card, weight, option) for card in options_weight_dict for weight, option in options_weight_dict[card].items()]
    if not tupled:
        if not hand:
            return None, None
        return hand[0], None
    card, _, option = max(tupled, key=lambda x: x[1])
    return card, option


def computer_event_loop(controller: Controller) -> Controller:
    if not controller.centre_updated:
        chosen_card, chosen_option = decide_option(controller)
        if chosen_card is None:
            print("ENCOUNTERED BUG")
            return rearrange_centre_cards(controller)
        if chosen_option is not None:
            if len(chosen_option) == len(controller.centre_cards):
                controller.upper_points = controller.upper_points + 1
        if not controller.chosen_card:
            controller.chosen_card = chosen_card
            controller.chosen_option = chosen_option
            controller.upper_cards.remove(chosen_card)
            chosen_card.flip()
            controller.holder = controller.holder + [chosen_card]
            return move_cards(controller, [chosen_card], True)
    else:
        controller.centre_updated = False
        chosen_option = controller.chosen_option
        if not chosen_option:
            controller.chosen_card = None
            controller.chosen_option = None
            controller.player_1_turn = True
            return rearrange_centre_cards(controller)
        for card_centre in chosen_option:
            controller.centre_cards.remove(card_centre)
        controller.centre_cards.remove(controller.chosen_card)
        controller = move_cards(controller, chosen_option + [controller.chosen_card])
        controller.chosen_card = None
        controller.chosen_option = None

    return rearrange_centre_cards(controller)


def game_logic(controller: Controller) -> Controller:
    # Only run the logic if not quitted and the game is explicitly running
    while not controller.quit and controller.game_running:
        if controller.empty and (len(controller.lower_cards) == 0 and len(controller.upper_cards) == 0):
            if controller.moveables:
                controller = move_cards(controller, list())
            elif (controller.centre_cards or not controller.holder) and not controller.wait_for_button:
                place = "lower" if controller.player_last_won else ""
                held = controller.centre_cards.copy()
                controller.holder = controller.holder + held
                controller.centre_cards = list()
                controller = move_cards(controller, held, False, place)
            # elif controller.chosen_option is not None:
            #     controller = computer_event_loop(controller)
            else:
                controller.game_running = False
        else:
            if controller.moveables:
                controller = move_cards(controller, list())
            elif controller.chosen_card and controller.chosen_option:
                controller = computer_event_loop(controller)
            elif controller.dealing or (len(controller.lower_cards) == 0 and len(controller.upper_cards) == 0 and not controller.wait_for_button):
                controller.dealing = True
                controller = deal_cards(controller)
                if len(controller.lower_cards) == 3 and len(controller.upper_cards) == 3:
                    if controller.first_deal:
                        if len(controller.centre_cards) < 4:
                            controller = deal_cards(controller, True)
                        else:
                            controller.first_deal = False
                            controller.dealing = False
                    else:
                        controller.dealing = False
                        if not controller.deck_values:
                            controller.empty = True
            elif not controller.player_1_turn and controller.upper_cards:
                controller = computer_event_loop(controller) # Delete if not working
            else:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        controller.quit = True
                        controller.game_running = False
                    elif controller.wait_for_button:
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            if event.button == 1:
                                for button in controller.buttons:
                                    if button.rect.collidepoint(event.pos):
                                        for card in button.option:
                                            controller.centre_cards.remove(card)
                                        if button.scopa:
                                            controller.lower_points = controller.lower_points + 1
                                        cards = button.option + [button.initial_card]
                                        controller = move_cards(controller, cards)
                                        controller.buttons = list()
                                        controller.wait_for_button = False
                    else:
                        if controller.player_1_turn:
                            controller = event_loop(event, controller.lower_cards, controller)
                        # else:
                        #     controller = computer_event_loop(controller)

        draw_controller(controller)
        pygame.display.update()

        controller.clock.tick(FPS)
    return controller


def score(controller: Controller) -> Tuple[Dict[str, int], Dict[str, int]]:
    def gold_tuples(hand: List[Card]) -> List[Tuple[int, str]]:
        return [c.tuple() for c in hand if c.suit == "Coins"]

    def cards(hand: List[Card]) -> str:
        length = len(hand)
        if length > 20:
            return "Win"
        elif length == 20:
            return "Draw"
        else:
            return "Lose"

    def coins(gold_tups: List[Tuple[int, str]]) -> str:
        length = len(gold_tups)
        if length > 5:
            return "Win"
        elif length == 5:
            return "Draw"
        else:
            return "Lose"

    def settebello(hand: List[Card]) -> str:
        return "Win" if (7, "Coins") in (card.tuple() for card in hand) else "Lose"

    def sevens(hand: List[Card]) -> str:
        seven = [card for card in hand if card.value == 7]
        if len(seven) > 2:
            return "Win"
        elif len(seven) == 2:
            sixes = [card for card in hand if card.value == 6]
            if len(sixes) > 2:
                return "Win"
            if len(sixes) == 2:
                return "Draw"
        else:
            return "Lose"

    def napola(gold_tups: List[Tuple[int, str]]) -> int:
        if all(card in gold_tups for card in NAPOLA_CARDS):
            for i in range(4, 11):
                if (i, "Coins") in gold_tups:
                    pass
                else:
                    return i-1
        return 0

    lower_scopa = controller.lower_points
    upper_scopa = controller.upper_points

    lower_hand = controller.lower_won_cards
    gold_tups = gold_tuples(lower_hand)

    lower_points = {"scopa": lower_scopa, "napola": napola(gold_tups)}
    upper_points = {"scopa": upper_scopa, "napola": napola(gold_tuples(controller.upper_won_cards))}

    for func in (cards, coins, sevens, settebello):
        if func == coins:
            result = func(gold_tups)
        else:
            result = func(lower_hand)
        if result == "Win":
            lower_points[func.__name__] = 1
            upper_points[func.__name__] = 0
        elif result == "Draw":
            lower_points[func.__name__] = 0
            upper_points[func.__name__] = 0
        else:
            lower_points[func.__name__] = 0
            upper_points[func.__name__] = 1
    return lower_points, upper_points


def find_winner(controller: Controller) -> Tuple[str, Dict[str, int], Dict[str, int]]:
    lower_scores, upper_scores = score(controller)
    lower_points = sum(lower_scores.values())
    upper_points = sum(upper_scores.values())
    if lower_points > upper_points:
        return "You", lower_scores, upper_scores
    elif lower_points < upper_points:
        return "Computer", lower_scores, upper_scores
    else:
        return "Draw", lower_scores, upper_scores


def win_logic(controller) -> Controller:
    winfont = pygame.font.SysFont(None, 80)
    pointfont = pygame.font.SysFont(None, 40)
    winner = ''
    text = ''
    left_surfaces = []
    right_surfaces = []
    while not controller.quit and not controller.restart:
        if not winner:
            winner, lower, upper = find_winner(controller)
            if winner == "You":
                text = "You win!"
            elif winner == "Computer":
                text = "You Lose :("
            else:
                text = "Draw!"
            lower_points = sum(lower.values())
            upper_points = sum(upper.values())
            point_text = f"Your points: {lower_points}, computer points: {upper_points}."
        restart_button = Button(WIDTH/2 - BUTTON_WIDTH/2, 2*HEIGHT/3, "Restart?")
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                controller.quit = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if restart_button.rect.collidepoint(event.pos):
                        controller.restart = True

        controller.screen.fill(GREEN)
        if not left_surfaces:
            for name, point in lower.items():
                left_surfaces.append(pointfont.render(f"{name}: {point}", False, (0, 0, 0)))
            for name, point in upper.items():
                right_surfaces.append(pointfont.render(f"{name}: {point}", False, (0, 0, 0)))
            left_surfaces = [pointfont.render("Your points:", False, (0, 0, 0))] + left_surfaces
            right_surfaces = [pointfont.render("Computer points:", False, (0, 0, 0))] + right_surfaces

        textsurface = winfont.render(text, False, (0, 0, 0))
        pointsurf = pointfont.render(point_text, False, (0, 0, 0))

        controller.screen.blit(textsurface, (WIDTH/2 - 160, HEIGHT/2 - 160))
        controller.screen.blit(pointsurf, (WIDTH / 2 - 240, 2*HEIGHT/3 - 80))
        for i in range(len(left_surfaces)):
            controller.screen.blit(left_surfaces[i], (WIDTH / 6 - 80, HEIGHT/6 + i * 80))
            controller.screen.blit(right_surfaces[i], (5*WIDTH / 6 - 80, HEIGHT / 6 + i * 80))
        restart_button.draw(controller.screen)
        pygame.display.update()
        pygame.display.flip()
        controller.clock.tick(60)
    return controller


def main():
    _build()
    screen = get_board()
    controller = Controller(screen=screen)
    while not controller.quit:
        controller = game_logic(controller)
        if controller.quit:
            break
        controller = win_logic(controller)
        if controller.restart:
            main()
            return


if __name__ == "__main__":
    # Initialise the font + pygame, otherwise hangs at first button.
    pygame.init()
    print(pygame.display.Info())
    pygame.font.SysFont(None, 30)
    main()
    pygame.quit()
    exit()
