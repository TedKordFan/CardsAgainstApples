from Config import Config
from Game import Game
from Player import Player

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, defer
from twisted.python import log

# system imports
import re, sys, time
from random import shuffle

class MessageLogger:
    def __init__(self, file):
        self.file = file

    def log(self, message):
        timestamp = time.strftime("[%H:%M:%S]", time.localtime(time.time()))
        self.file.write('%s %s\n' % (timestamp, message))
        self.file.flush()

    def close(self):
        self.file.close()


class DealerBot(irc.IRCClient):
    nickname = "dealer"
    channel_default = Config.CHANNEL_DEFAULT

    game = None
    playerqueue = {}
    joinindex = 0
    whoisinfo = {}

    def isQueued(self, nick):
        for k, v in self.playerqueue.iteritems():
            if nick == v.nick:
                return True
        return False

    def doHand(self, tokens, source, user):
        if self.game is not None:
            player = self.game.getPlayer(user)
            if player is not None:          
                msg = "Your cards: " + player.handToString() + ". Play a card by typing \"send <number>\"."
                self.msg(user, msg)

    def doJoin(self, tokens, source, user):
        if not self.isQueued(user) and source != self.nickname: # Ignore joiner who has already joined; no joining games from PM
            if self.game is not None:
                self.msg(user, "Game is currently in progress. Please wait until it has finished and join the next one!")
            elif len(self.playerqueue) >= Config.PLAYERS_MAX:
                msg = user + ": No more than " + str(Config.PLAYERS_MAX) + " players permitted."
                self.msg(self.channel_default, msg)
            else:
                d = self.whois(user)
                d.addCallback(self.addPlayer, user)

    def doPlayers(self, tokens, source, user):
        msg = user + ": "
        if self.game is not None:
            msg += "There is a game in progress. There are currently " + str(self.game.getPlayerCount())
            msg += " playing: " + self.game.playersToString() + ". The current question-setter is " + self.game.getSetter().nick + "."
        else:
            msg += "There is no game in progress. There are currently " + str(len(self.playerqueue)) + " players waiting for a game to begin."
        self.msg(self.channel_default, msg)

    def doQuit(self, tokens, source, user):
        if self.isQueued(user): # Game has not started, but player in queue wishes to quit
            for k, player in self.playerqueue.iteritems():
                if player.nick == user:
                    del self.playerqueue[k]
                    break
            msg = user + " has left the game. "
            if not self.playerqueue:
                msg += "No players remaining."
            else:
                msg += str(len(self.playerqueue)) + " player(s) remaining."
            self.msg(self.channel_default, msg)
            #self.mode(self.channel_default, False, "v", None, user)
        elif self.game is not None and self.game.isPlayer(user): # Game has started, player wishes to quit
            self.game.removePlayer(user)
            remaining = self.game.getPlayerCount()
            msg = user + " has left the game. "
            if remaining == 0:
                msg += "No players remaining."
                # Handle this
            elif remaining == 1:
                msg += "Only one player remaining."
                # Handle this - declare them the winner
            else:
                msg += str(self.game.getPlayerCount()) + " player(s) remaining."
            self.msg(self.channel_default, msg)
            #self.mode(self.channel_default, False, "v", None, user)

    def doScore(self, tokens, source, user):
        if self.game is not None:
            msg = user + ": Current scores: " + self.game.scoresToString()
            self.msg(self.channel_default, msg)
            print msg

    def doSelect(self, tokens, source, user):
        if self.game is not None:
            player = self.game.getPlayer(user)
            if player is not None:
                if player is self.game.getSetter():
                    msg = ""
                    winningcard = None
                    if not self.game.answersReady():
                        msg = "Not all answers have been received yet. Be patient!"
                    elif len(tokens) < 2:
                        msg = "You have to tell me which card you want to select."
                    else:
                        possible = self.game.played
                        try:
                            index = int(tokens[1])
                            if index < 1 or index > len(possible):
                                msg = "Please select a card number from 1 to " + str(len(possible)) + ", inclusive."
                            else:
                                winningcard = self.game.played[index-1]
                                msg = "You have selected card #" + str(index) + ": \"" + winningcard[0] + "\"."                                
                        except:
                            msg = "Please select an actual number, from 1 to " + str(len(possible)) + ", inclusive."
                    self.msg(user, msg)
                    if winningcard is not None:
                        self.awardWin(winningcard)
                        if self.game.toContinue():
                            self.game.resetRound()
                            #self.endGame()
                            self.round()
                        else:
                            self.endGame()
                else:
                    msg = "You are not the question-setter!"
                    self.msg(user, msg)

    def doSend(self, tokens, source, user):
        if self.game is not None:
            player = self.game.getPlayer(user)
            if player is not None:
                msg = ""
                if player is not self.game.getSetter():
                    if player.acard_played is not None:
                        msg = "You have already played a card."
                    elif len(tokens) < 2:
                        msg = "You have to tell me which card you want to send."
                    else:
                        available = len(player.acards_held)
                        try:
                            index = int(tokens[1])
                            if index < 1 or index > available:
                                msg = "Please select a card number from 1 to " + str(available) + ", inclusive."
                            else:
                                sending = player.acards_held[index-1]
                                player.acard_played = sending
                                self.game.played.append((sending, player))
                                msg = "You have sent card #" + str(index) + ": \"" + sending + "\"."
                        except:
                            msg = "Please select an actual number, from 1 to " + str(available) + ", inclusive."
                    self.msg(user, msg)
                    if self.game.answersReady():
                        shuffle(self.game.played) # Shuffle the potential answers for the question-setter
                        self.printSentToSetter()
                else:
                    msg = "You may not send an answer, as you are setting the question!"
                    self.msg(user, msg)

    def doStart(self, tokens, source, user):
        # Someone attempts to start  
        if self.isQueued(user) and source != self.nickname: # Only players may start a game; no starting games from PM
            if len(self.playerqueue) < Config.PLAYERS_MIN:
                msg = user + ": Minimum of " + str(Config.PLAYERS_MIN) + " players required to start a game."
                self.msg(self.channel_default, msg)
            else:
                self.game = Game(self.playerqueue)
                self.msg(self.channel_default, self.game.getWelcome())
                self.playerqueue = {}        

                # prototype
                self.round()

                # the actual loop (not testing here)
                #while self.game.toContinue():
                #    self.round(channel)

               #self.endGame(channel)

    def doStats(self, tokens, source, user):
        pass

    def round(self):
        setter = self.game.getSetter()
        question = self.game.dealQuestion()
        msg = setter.nick + " asks: " + question
        self.topic(self.channel_default, msg)
        # await responses
        # wait for setterto select winner
        # self.game.updateSetter()
        # return

    def addPlayer(self, mask, nick):
        self.playerqueue[self.joinindex] = Player(mask, nick)
        self.joinindex += 1
        print nick + " joining."
        for k, player in self.playerqueue.iteritems():
          print player.nick + " " + player.hostmask
        msg = nick + " has joined the game and raised the number of players to " + str(len(self.playerqueue)) + "."
        self.msg(self.channel_default, msg)
        # this works, but commenting out during testing to reduce spam
        #self.mode(self.channel_default, True, "v", None, nick)

    def endGame(self):
        self.msg(self.channel_default, "Game over!")
        self.printWinner()
        for order, player in self.game.players_byorder.iteritems():
            self.mode(self.channel_default, False, "v", None, player.nick)
        self.topic(self.channel_default, Config.TOPIC_DEFAULT)
        self.game = None
        self.joinindex = 0

    commands = { "exit" : doQuit,
                 "hand" : doHand,
                 "j" : doJoin,
                 "join" : doJoin,
                 "leave" : doQuit,
                 "players" : doPlayers,
                 "q" : doQuit,
                 "quit" : doQuit,
                 "score" : doScore,
                 "scores" : doScore,
                 "select" : doSelect,
                 "send" : doSend,
                 "start" : doStart,
                 "stats" : doStats }

    def printWinner(self):
        winners, winningscore = self.game.getWinners()
        msg = ""

        if winners is not None and winningscore > 0:
            if len(winners) == 1:
                msg = "The winner is: " + winners[0].nick + " with " + str(winningscore) + " points!"
            else:
                msg = "There are " + str(len(winners)) + " players tied as winner: "
                for i in range(len(winners)-1):
                    msg += winners[i].nick + ", "
                msg += "and " + winners[len(winners)-1].nick + ", all on " + str(winningscore) + " points!"
        else:
            msg = "There were no winners in this game."

        self.msg(self.channel_default, msg)

    def printSentToSetter(self):
        setter = self.game.getSetter()
        msg = "Please select one of the following by typing \"select <number>\": "
        for i in range(len(self.game.played)):
            msg += "[" + str(i+1) + "] " + self.game.played[i][0] + ", "
        msg = msg[:-2] + "."
        self.msg(setter.nick, msg)

    def printSentToChannel(self):
        msg = "The available choices were: "
        for i in range(len(self.game.played)):
            msg += "[" + self.game.played[i][1].nick + "] " + self.game.played[i][0] + ", "
        msg = msg[:-2] + "."
        self.msg(self.channel_default, msg)

    def awardWin(self, winningcard):
        card = winningcard[0]
        player = winningcard[1]
        self.game.awardQuestion(player, card)
        self.printSentToChannel()
        msg = "The winning answer was " + player.nick + "'s: \"" + card + "\"."
        self.msg(self.channel_default, msg)

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.logger = MessageLogger(open(self.factory.filename, "a"))
        self.logger.log("[connected at %s]" % 
                        time.asctime(time.localtime(time.time())))


    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.logger.log("[disconnected at %s]" % 
                        time.asctime(time.localtime(time.time())))
        self.logger.close()


    # Whois wrapper
    def whois(self, nick):
        d = defer.Deferred()
        if nick in self.whoisinfo:
            ds = self.whoisinfo[nick][0]
            ds.append(d)
            return d
  
        info = {}
        self.whoisinfo[nick] = [[d], info]
        irc.IRCClient.whois(self, nick, None)
        return d

    # callbacks for events

    def irc_RPL_WHOISUSER(self, prefix, params):
        nick = params[1]
        mask = params[2] + '@' + params[3]
        self.whoisinfo[nick][1] = mask

  
    def irc_RPL_ENDOFWHOIS(self, prefix, params):
        nick = params[1].lower()
        if nick in self.whoisinfo:
            ds = self.whoisinfo[nick][0]
            info = self.whoisinfo[nick][1]
            del self.whoisinfo[nick]
            [d.callback(info) for d in ds]


    def signedOn(self):
        self.join(self.factory.channel)


    def privmsg(self, user, channel, msg):
        user = user.split('!', 1)[0]
        self.logger.log("<%s> %s" % (user, msg))
        
        tokens = re.split(' *', msg.strip())

        # Check to see if they're sending a private message
        # These are the same as messages in channel with trigger, except that here trigger is not needed
        if channel == self.nickname:
            cmd = tokens[0]
            if cmd in self.commands:
                self.commands[cmd](self, tokens, channel, user)            

        # Check whether it starts with trigger
        elif msg.startswith(Config.TRIGGER):
            cmd = tokens[0][len(Config.TRIGGER):]
            if cmd in self.commands:
                self.commands[cmd](self, tokens, channel, user)

        # Otherwise check to see if it is a message directed at me
        #if msg.startswith(self.nickname + ":"):
        #    msg = "%s: lol" % user
        #    self.msg(channel, msg)
        #    self.logger.log("<%s> %s" % (self.nickname, msg))


    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        user = user.split('!', 1)[0]
        self.logger.log("* %s %s" % (user, msg))


    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        self.logger.log("%s is now known as %s" % (old_nick, new_nick))


    def alterCollidedNick(self, nickname):
        return nickname + '^'


class DealerBotFactory(protocol.ClientFactory):
    def __init__(self, channel, filename):
        self.channel = channel
        self.filename = filename

    def buildProtocol(self, addr):
        p = DealerBot()
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()


if __name__ == '__main__':
    # initialize logging
    log.startLogging(sys.stdout)
   
    if len(sys.argv) < 4:
      print "Usage: " + sys.argv[0] + " <network> <channel> <logfile>"
    # create factory protocol and application
    f = DealerBotFactory(sys.argv[2], sys.argv[3])

    # connect factory to this host and port
    reactor.connectTCP(sys.argv[1], 6667, f)

    # run bot
    reactor.run()
