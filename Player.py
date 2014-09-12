class Player:

    def __init__(self, hostmask, nick):
        self.hostmask = hostmask
        self.nick = nick
        self.acard_played = None
        self.qcards_won = []
        self.acards_held = []

    def addCard(self, card):
        self.acards_held.append(card)

    def awardQuestion(self, card): 
        self.qcards_won.append(card)

    def handToString(self):
        hand = ""
        for i in range(len(self.acards_held)):
            hand += "[" + str(i+1) + "] " + self.acards_held[i] + ", "
        return hand[:-2]

    def getScore(self):
        return len(self.qcards_won)
