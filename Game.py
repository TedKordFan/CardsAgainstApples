from Config import Config
from Deck import Deck
from Player import Player

class Game:

    # Initialise game
    def __init__(self, players):
        self.players = players
        self.answers = Deck(Config.FILENAME_ANSWERS)
        self.questions = Deck(Config.FILENAME_QUESTIONS)
        self.winner = None

        self.ids = []
        for order, player in self.players.iteritems():
            for i in range(Config.HAND_SIZE):
                player.addCard(self.answers.take()) # Deal initial hand to each player
            self.ids.append(order)

        for order, player in players.iteritems():
            print player.nick + " " + repr(player.acards_held)

    def dealAnswer(nick):
        for order, player in self.players.iteritems():
            if player.nick == nick:
                player.addCard(self.answers.take())

    def awardQuestion(nick, card):
        for order, player in self.players.iteritems(): 
            if player.nick == nick:
                player.qcards_won.add(card)
