class Player:
	def __init__(self, hostmask, nick):
		self.hostmask = hostmask
		self.nick = nick
		self.acard_played = None
		self.qcards_won = set
		self.acards_held = []

	def addCard(self, card):
		self.acards_held.append(card)
