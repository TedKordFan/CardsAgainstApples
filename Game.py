from Config import Config
from Deck import Deck
from Player import Player

class Game:

    # Initialise game
    def __init__(self, players):
        self.players_byorder = players # Join order mapped to players

        self.players_bynick = {} # Current nick mapped to players
        for order, player in players.iteritems():
            self.players_bynick[player.nick] = player

        self.answers = Deck(Config.FILENAME_ANSWERS)
        self.questions = Deck(Config.FILENAME_QUESTIONS)
        self.winner = None

        self.ids = []
        for order, player in self.players_byorder.iteritems():
            for i in range(Config.HAND_SIZE):
                player.addCard(self.answers.take()) # Deal initial hand to each player
            self.ids.append(order)

        self.idindex = 0

    # Ensures that there is no winner yet, and that there are appropriate numbers of players, questions, and answers remaining
    def toContinue(self):
        return self.winner is None and len(self.questions.cards) > 0 and len(self.players_bynick) >= 2 and len(self.players_bynick) < len(self.answers.cards)

    def dealAnswer(self, nick):
        self.players_bynick[nick].addCard(self.answers.take())

    def dealQuestion(self):
        return self.questions.take()

    def awardQuestion(self, nick, card):
        winner = self.players_bynick[nick]
        winner.qcards_won.add(card)
        if len(winner.qcards_won) >= Config.GOAL:
            self.winner = winner

    def getWelcome(self):
        msg = ""
        for k, player in self.players_byorder.iteritems():
            msg += player.nick + ", "
        return msg[:-2]

    def getPlayer(self, nick):
        if nick in self.players_bynick:
            return self.players_bynick[nick]
        return None

    def getNextSetter(self):
        id = self.ids[self.idindex]
        setter = self.players_byorder[id]
        print "[Game] returning next setter: (player " + str(id) + ") " + setter.nick
        self.idindex = (self.idindex + 1) % len(self.ids)
        return setter

    def getWinners(self):

        if self.winner is not None:
            return [self.winner]

        if not self.players_bynick:
           return []

        curwinners = []
        curscore = 0
        for nick, player in self.players_bynick.iteritems():
            playerscore = len(player.qcards_won)
            if not curwinners:
                curwinners.append(player)
                curscore = playerscore
            elif playerscore == curscore:
                curwinners.append(player)
            elif playerscore > curscore:
                curwinners = [player]
                curscore = playerscore

        return curwinners
