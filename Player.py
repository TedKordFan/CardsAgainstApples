class Player:

    def __init__(self, hostmask, nick):
        self.hostmask = hostmask
        self.nick = nick
        self.acard_played = None
        self.qcards_won = set
        self.acards_held = []

    def addCard(self, card):
        self.acards_held.append(card)

    def handToString(self):
        hand = ""
        for i in range(len(self.acards_held)):
            hand += "[" + str(i+1) + "] " + self.acards_held[i] + ", "
        return hand[:-2]
