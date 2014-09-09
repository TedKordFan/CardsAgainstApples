from Configuration import Config
from Decks import Decks
from Player import Player

def start(players):
	decks = Decks()

	ids = []

	for order, player in players.iteritems():
		ids.append(order)
		for i in range(Config.HAND_SIZE):
			player.addCard(decks.getAnswer())

	for order, player in players.iteritems():
		print player.nick + " " + repr(player.acards_held)

	winner = None
	idindex = 0
	while len(players) >= 2 and len(players) < len(decks.answers) and winner is None:
		id = ids[idindex]
		print "current question asker: " + str(id) + ":" + players[id].nick
		question = decks.getQuestion()
		if question is None:
			break
		print question
		idindex = (idindex + 1) % len(ids)
			
def main():
	players = {	0:Player("mollusc@oce.an", "mollusc"),
							1:Player("deneb@aqui.la", "eagle")}
	start(players)

main()
