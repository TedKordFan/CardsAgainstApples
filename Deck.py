from random import shuffle

class Deck:

	# Construct a deck of cards
	def __init__(self, filepath):

		cardfile = open(filepath, 'r')

		self.cards = []
		for card in cardfile:
			self.cards.append(card.strip())

		cardfile.close()

		shuffle(self.cards)


	# Return the next available card, popping it from the deck
	def take(self):
		if self.cards:
			return self.cards.pop()
