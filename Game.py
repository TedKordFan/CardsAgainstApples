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
        self.setter = self.players_byorder[self.ids[self.idindex]] # Current question-setter
        self.played = [] # List of tuples, each tuple composed of a card and the player that played it

    def resetRound(self):
        for nick, player in self.players_bynick.iteritems():
            if player.acard_played is not None:
                player.acards_held.remove(player.acard_played)
                player.acard_played = None
                self.dealAnswer(nick)
        self.played = []
        self.updateSetter()

    # Ensures that there is no winner yet, and that there are appropriate numbers of players, questions, and answers remaining
    def toContinue(self):
        return self.winner is None and len(self.questions.cards) > 0 and len(self.players_bynick) >= 2 and len(self.players_bynick) < len(self.answers.cards)

    def dealAnswer(self, nick):
        self.players_bynick[nick].addCard(self.answers.take())

    def dealQuestion(self):
        return self.questions.take()

    def awardQuestion(self, winner, card):
        winner.awardQuestion(card)
        if len(winner.qcards_won) >= Config.GOAL:
            self.winner = winner

    def answersReady(self):
        return len(self.played) == (len(self.players_byorder)-1) # Is this too brittle? Need to check every player maybe?

    def getWelcome(self):
        msg = ""
        for k, player in self.players_byorder.iteritems():
            msg += player.nick + ", "
        return msg[:-2] + ": Welcome to Cards Against Apples!"

    def scoresToString(self):
        msg = ""
        for k, player in self.players_byorder.iteritems():
            msg += player.nick + ": " + str(player.getScore()) + ", "
        return msg[:-2]

    def isPlayer(self, nick):
        return nick in self.players_bynick

    def removePlayer(self, nick):
        player = self.players_bynick[nick]

        if self.setter == player:
            self.updateSetter()

        del self.players_bynick[nick]
        id_todelete = -1
        for order, player in self.players_byorder.iteritems():
            if nick == player.nick:
                id_todelete = order
                del self.players_byorder[order]
                break
        for id in self.ids:
            if id_todelete == id:
                self.ids.remove(id)
                break

    def getPlayerCount(self):
        return len(self.players_byorder)

    def playersToString(self):
        msg = ""
        for i in range(len(self.ids)-1):
            msg += self.players_byorder[self.ids[i]].nick + ", "
        msg += "and " + self.players_byorder[self.ids[len(self.ids)-1]].nick
        return msg

    def getPlayer(self, nick):
        if nick in self.players_bynick:
            return self.players_bynick[nick]
        return None

    def getSetter(self):
        return self.setter

    # Update current question-setter
    def updateSetter(self):
        self.idindex = (self.idindex + 1) % len(self.ids)
        id = self.ids[self.idindex]
        setter = self.players_byorder[id]
        print "[Game] next setter: (player " + str(id) + ") " + setter.nick
        self.setter = setter

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

        return curwinners, curscore
