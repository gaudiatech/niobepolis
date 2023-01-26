import common
from uth_model import UthModel, PokerStates


kengi = common.kengi
pygame = kengi.pygame
MyEvTypes = common.MyEvTypes

# Aliases .............
Card = kengi.tabletop.StandardCard
PokerHand = kengi.tabletop.PokerHand
StandardCard = kengi.tabletop.StandardCard

# constants
CHIP_SIZE_PX = (33, 33)
BACKGROUND_IMG_PATH = 'user_assets/pokerbackground3.png'
OFFSET_CASH = (-48, -24)

CARD_SLOTS_POS = {  # coords in pixel -> where to place cards/chips
    'dealer1': (140, 48),
    'dealer2': (140 + 40, 48),
    'player1': (140, 206),
    'player2': (140 + 40, 206),
    'flop3': (238 - 40 * 2, 115),
    'flop2': (238 - 40 * 1, 115),
    'flop1': (238, 115),
    'river': (110 - 40, 115),
    'turn': (110, 115),
}

MONEY_POS = {
    'ante': (45, 166),
    'blind': (90, 166),

    # 'blind': (1040 / 3, 757 / 3),
    'raise1': (955 / 3, 870 / 3),
    'raise2': (961 / 3, 871 / 3),
    'raise3': (967 / 3, 872 / 3),
    'raise4': (973 / 3, 873 / 3),
    'raise5': (980 / 3, 875 / 3),
    'raise6': (986 / 3, 876 / 3)
}
PLAYER_CHIPS = {
    '2a': (825 / 2, 1000 / 2),
    '2b': (905 / 2, 1000 / 2),
    '5': (985 / 2, 1000 / 2),
    '10': (1065 / 2, 1000 / 2),
    '20': (1145 / 2, 1000 / 2)
}


class UthView(kengi.EvListener):
    TEXTCOLOR = kengi.pal.punk['flashypink']  # (5, 58, 7)
    BG_TEXTCOLOR = (92, 92, 100)
    ASK_SELECTION_MSG = 'SELECT ONE OPTION: '

    def __init__(self, model):
        super().__init__()
        self.bg = None
        self._my_assets = dict()

        self.chip_spr = dict()
        self.chip_adhoc_image = None

        self._assets_rdy = False
        self._mod = model
        self.small_ft = kengi.pygame.font.Font(None, 24)
        self.info_msg0 = None
        self.info_msg1 = None  # will be used to tell the player what he/she has to do!
        self.info_msg2 = None

        self.ante_etq = None
        self.blind_etq = None
        self.cash_etq = None
        self.on_money_update(None)  # force update

        self.scrsize = kengi.get_surface().get_size()
        self.midscreen_pt = [
            self.scrsize[0]//2,
            self.scrsize[1]//2
        ]

    def on_chip_update(self, ev):
        print('[View] reception chipval update :::', ev.value)
        self.chip_adhoc_image = self.chip_spr[str(ev.value)].image

    def on_keydown(self, ev):
        omega = (2, 5, 10, 20)
        curridx = omega.index(self._mod.get_chipvalue())
        ch = False

        if ev.key == pygame.K_DOWN:
            curridx -= 1
            if curridx < 0:
                curridx = len(omega)-1
            ch = True
        elif ev.key == pygame.K_UP:
            curridx = (curridx+1) % len(omega)
            ch = True

        if ch:
            y = omega[curridx]
            self._mod.set_chipvalue(y)

    def _load_assets(self):
        self.bg = kengi.pygame.image.load(BACKGROUND_IMG_PATH)
        spr_sheet = kengi.gfx.JsonBasedSprSheet('user_assets/pxart-french-cards')
        self._my_assets['card_back'] = spr_sheet[
            'back-blue.png']  # pygame.transform.scale(spr_sheet['back-of-card.png'], CARD_SIZE_PX)
        for card_cod in StandardCard.all_card_codes():
            y = PokerHand.adhoc_mapping(card_cod[0]).lstrip('0') + card_cod[1].upper()  # convert card code to path
            self._my_assets[card_cod] = spr_sheet[
                f'{y}.png']  # pygame.transform.scale(spr_sheet[f'{y}.png'], CARD_SIZE_PX)
        spr_sheet2 = kengi.gfx.JsonBasedSprSheet('user_assets/pokerchips')
        for chip_val_info in ('2a', '2b', '5', '10', '20'):
            y = {
                '2a': 'chip02.png',
                '2b': 'chip02.png',
                '5': 'chip05.png',
                '10': 'chip10.png',
                '20': 'chip20.png'
            }[chip_val_info]  # adapt filename

            # no chip rescaling:
            # tempimg = spr_sheet2[y]
            # chip rescaling:
            tempimg = pygame.transform.scale(spr_sheet2[y], CHIP_SIZE_PX)

            # tempimg.set_colorkey((255, 0, 255))
            spr = kengi.pygame.sprite.Sprite()
            spr.image = tempimg
            spr.rect = spr.image.get_rect()
            spr.rect.center = PLAYER_CHIPS[chip_val_info]
            self.chip_spr['2' if chip_val_info in ('2a', '2b') else chip_val_info] = spr

        self.chip_adhoc_image = self.chip_spr['2'].image

        self._assets_rdy = True

    def on_state_changes(self, ev):
        if self._mod.stage == PokerStates.AnteSelection:
            self.info_msg0 = self.small_ft.render('Press BACKSPACE to begin', False, self.TEXTCOLOR, self.BG_TEXTCOLOR)
            self.info_msg1 = None
            self.info_msg2 = None
        else:
            msg = None
            if self._mod.stage == PokerStates.PreFlop:
                msg = ' CHECK, BET x3, BET x4'
            elif self._mod.stage == PokerStates.Flop:
                msg = ' CHECK, BET x2'
            elif self._mod.stage == PokerStates.TurnRiver:
                msg = ' FOLD, BET x1'
            if msg:
                self.info_msg0 = self.small_ft.render(self.ASK_SELECTION_MSG, False, self.TEXTCOLOR, self.BG_TEXTCOLOR)
                self.info_msg1 = self.small_ft.render(msg, False, self.TEXTCOLOR, self.BG_TEXTCOLOR)
            # TODO display the amount lost

    def on_mousedown(self, ev):
        self._mod.wallet.stake_chip()

    def on_money_update(self, ev):  # , fvalue=None):  # RE-draw cash value
        # x = self._mod.chipvalue
        x = self._mod.get_balance()
        _, antev, blindv, _ = self._mod.get_all_bets()

        self.ante_etq = self.small_ft.render(f'%d$ ' % antev, False, self.TEXTCOLOR)
        self.blind_etq = self.small_ft.render(f'%d$ ' % blindv, False, self.TEXTCOLOR)

        self.cash_etq = self.small_ft.render(f'%d$ ' % x, False, self.TEXTCOLOR)

    def on_victory(self, ev):
        result = ev.amount
        infoh_player = self._mod.player_vhand.description
        infoh_dealer = self._mod.dealer_vhand.description
        msg = f"Player: {infoh_player}; Dealer: {infoh_dealer}; Change {result}$"
        self.info_msg0 = self.small_ft.render('Victory!', False, self.TEXTCOLOR)
        self.info_msg1 = self.small_ft.render(msg, False, self.TEXTCOLOR)
        self.info_msg2 = self.small_ft.render('BACKSPACE to restart', False, self.TEXTCOLOR)

    def on_tie(self, ev):
        self.info_msg0 = self.small_ft.render('Its a Tie.', True, self.TEXTCOLOR)
        infoh_player = self._mod.player_vhand.description
        infoh_dealer = self._mod.dealer_vhand.description
        self.info_msg1 = self.small_ft.render(
            f"Player: {infoh_player}; Dealer: {infoh_dealer}; Change {0}$",
            True, self.TEXTCOLOR
        )
        self.info_msg2 = self.small_ft.render('BACKSPACE to restart', False, self.TEXTCOLOR)

    def on_defeat(self, ev):
        if self._mod.folded:
            msg = 'Player folded.'
        else:
            msg = 'Defeat.'
        self.info_msg0 = self.small_ft.render(msg, True, self.TEXTCOLOR)
        result = ev.loss
        if self._mod.folded:
            self.info_msg1 = self.small_ft.render(f"You lost {result}$", False, self.TEXTCOLOR)
        else:
            infoh_dealer = self._mod.dealer_vhand.description
            infoh_player = self._mod.player_vhand.description
            self.info_msg1 = self.small_ft.render(
                f"Player: {infoh_player}; Dealer: {infoh_dealer}; You've lost {result}$", False, self.TEXTCOLOR
            )
        self.info_msg2 = self.small_ft.render('BACKSPACE to restart', False, self.TEXTCOLOR)

    @staticmethod
    def centerblit(refscr, surf, p):
        w, h = surf.get_size()
        refscr.blit(surf, (p[0] - w // 2, p[1] - h // 2))

    def _paint(self, refscr):
        refscr.blit(self.bg, (0, 0))
        cardback = self._my_assets['card_back']

        # ---------- draw chip value if the phase is still "setante"
        if self._mod.stage == PokerStates.AnteSelection:
            target_pt = (
                self.midscreen_pt[0],
                self.midscreen_pt[1] + 100
            )
            UthView.centerblit(refscr, self.chip_adhoc_image, target_pt)

            refscr.blit(self.ante_etq, MONEY_POS['ante'])
            refscr.blit(self.blind_etq, MONEY_POS['blind'])

        if self._mod.stage != PokerStates.AnteSelection:  # draw all cards, unless the state is AnteSelection
            for loc in CARD_SLOTS_POS.keys():
                if self._mod.visibility[loc]:
                    desc = self._mod.get_card_code(loc)
                    x = self._my_assets[desc]
                else:
                    x = cardback
                UthView.centerblit(refscr, x, CARD_SLOTS_POS[loc])

        # -- draw amounts for ante, blind and the bet
        # for info_e in self._mod.money_info:
        #     x, name = info_e
        #     lbl_surf = self.small_ft.render(f'{x}', True, self.TEXTCOLOR, self.BG_TEXTCOLOR)
        #     refscr.blit(lbl_surf, CARD_SLOTS_POS[name])

        # -- draw chips & the total cash amount
        for k, v in enumerate((2, 5, 10, 20)):
            adhoc_spr = self.chip_spr[str(v)]
            if v == 2:
                adhoc_spr.rect.center = PLAYER_CHIPS['2b']
            refscr.blit(adhoc_spr.image, adhoc_spr.rect.topleft)
        self.chip_spr['2'].rect.center = PLAYER_CHIPS['2a']
        refscr.blit(self.chip_spr['2'].image, self.chip_spr['2'].rect.topleft)
        refscr.blit(self.cash_etq, (self.scrsize[0]+OFFSET_CASH[0], self.scrsize[1]+OFFSET_CASH[1]))

        # -- display all 3 prompt messages
        for rank, e in enumerate((self.info_msg0, self.info_msg1, self.info_msg2)):
            if e is not None:
                refscr.blit(e, (24, 10 + 50 * rank))

    def on_paint(self, ev):
        if not self._assets_rdy:
            self._load_assets()
        self._paint(ev.screen)
