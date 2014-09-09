from Config import Config
from Game import Game
from Player import Player

# Start game
def start(players):
	game = Game(players)
	game.play()
			
# Create game parameters
def main():

	# register the joining/quitting of players
	# enforce minimum/maximum player numbers

	players = {	0:Player("mollusc@oce.an", "mollusc"),
							1:Player("deneb@aqui.la", "eagle"),
							3:Player("troll@under.bridge", "trole"),
							7:Player("pegasus@olympia", "horsie")}
	start(players)

main()
