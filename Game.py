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

	# Play game
	def play(self):

		idindex = 0
		while len(self.players) >= 2 and len(self.players) < len(self.answers.cards) and self.winner is None:
			id = self.ids[idindex]

			question = self.questions.take()
			if question is None:
				break

			print "(player " + str(id) + ") " + self.players[id].nick + " asks: " + question

			idindex = (idindex + 1) % len(self.ids)

