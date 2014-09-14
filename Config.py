class Config:
	TRIGGER = '!'

	PLAYERS_MIN = 3 # min number of players before a game may start
	PLAYERS_MAX = 30 # max number of players (mainly so game doesn't run out of cards)
	HAND_SIZE = 8 # size of a hand (number of cards each player should have at a time)
	GOAL = 5 # when a player wins this number of question cards, the game ends with them as the winner
	IDLE_TIME = 240 # how long player can say nothing in channel before they get kicked out of game
	IDLE_WARNING = 120 # how long player can say nothing in channel before they are warned that they must speak; strictly less than IDLE_TIME
	SEND_TIME = 180 # answering players have this long to send a response after a round has started
	SELECT_TIME = 180 # questioning player has this long to select the winning answer after all answers are received (or SEND_TIME is reached)
	FILENAME_ANSWERS = 'answers.txt'
	FILENAME_QUESTIONS = 'questions.txt'
        TOPIC_DEFAULT = 'join: !j'
        CHANNEL_DEFAULT = '#caa'
