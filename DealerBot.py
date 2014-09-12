from Config import Config
from Game import Game
from Player import Player

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, defer
from twisted.python import log

# system imports
import time, sys

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

    game = None
    playerqueue = {}
    joinindex = 0
    whoisinfo = {}

    def isQueued(self, nick):
        for k, v in self.playerqueue.iteritems():
            if nick == v.nick:
                return True
        return False

    def doHand(self, msg, channel, user):
        if self.game is not None:
            player = self.game.getPlayer(user)
            if player is not None:          
                msg = "Your cards: " + player.handToString()  
                self.msg(user, msg)

    def doJoin(self, msg, channel, user):
        if not self.isQueued(user): # Ignore joiner who has already joined
            if self.game is not None:
                self.msg(user, "Game is currently in progress. Please wait until it has finished and join the next one!")
            elif len(self.playerqueue) >= Config.PLAYERS_MAX:
                msg = user + ": No more than " + str(Config.PLAYERS_MAX) + " players permitted."
                self.msg(channel, msg)
            else:
                d = self.whois(user)
                d.addCallback(self.addPlayer, user, channel)

    def doQuit(self, msg, channel, user):
        if self.isQueued(user): # Ignore quitter who is not already playing
            for k, player in self.playerqueue.iteritems():
                if player.nick == user:
                    del self.playerqueue[k]
                    break
            msg = user + " has left the game. "
            if not self.playerqueue:
                msg += "No players remaining."
            else:
                msg += str(len(self.playerqueue)) + " player(s) remaining."
            self.msg(channel, msg)

    def doScore(self, msg, channel, user):
        if self.game is not None:
            msg = user + ": Current scores: " + self.game.scoresToString()
            self.msg(channel, msg)
            print msg

    def doSelect(self, msg, channel, user):
        pass

    def doSend(self, msg, channel, user):
        pass

    def doStart(self, msg, channel, user):
        # Someone attempts to start  
        if self.isQueued(user): # Only players may start a game
            if len(self.playerqueue) < Config.PLAYERS_MIN:
                msg = user + ": Minimum of " + str(Config.PLAYERS_MIN) + " players required to start a game."
                self.msg(channel, msg)
            else:
                self.game = Game(self.playerqueue)
                self.msg(channel, self.game.getWelcome())
                self.playerqueue = {}        

                # prototype
                setter = self.game.getNextSetter()
                question = self.game.dealQuestion()
                msg = setter.nick + " asks: " + question
                self.msg(channel, msg)

                # the actual loop (not testing here)
                #while self.game.toContinue():
                #    setter = self.game.getNextSetter()
                #    question = self.game.dealQuestion()
                #    print "[Bot] " + setter.nick + " asks: " + question


    def doStats(self, msg, channel, user):
        pass    


    def addPlayer(self, mask, nick, channel):
        self.playerqueue[self.joinindex] = Player(mask, nick)
        self.joinindex += 1
        print nick + " joining."
        for k, player in self.playerqueue.iteritems():
          print player.nick + " " + player.hostmask
        msg = nick + " has joined the game and raised the number of players to " + str(len(self.playerqueue)) + "."
        self.msg(channel, msg)


    commands = { "exit" : doQuit,
                 "hand" : doHand,
                 "j" : doJoin,
                 "join" : doJoin,
                 "leave" : doQuit,
                 "q" : doQuit,
                 "quit" : doQuit,
                 "score" : doScore,
                 "scores" : doScore,
                 "select" : doSelect,
                 "send" : doSend,
                 "start" : doStart,
                 "stats" : doStats }


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
        
        # Check to see if they're sending a private message
        # These are the same as messages in channel with trigger, except that here trigger is not needed
        if channel == self.nickname:
            cmd = msg.split(' ')[0]
            if cmd in self.commands:
                self.commands[cmd](self, msg, channel, user)            

        # Otherwise check to see if it is a message directed at me
        #if msg.startswith(self.nickname + ":"):
        #    msg = "%s: lol" % user
        #    self.msg(channel, msg)
        #    self.logger.log("<%s> %s" % (self.nickname, msg))

        # Check whether it starts with trigger
        if msg.startswith(Config.TRIGGER):
            cmd = msg.split(' ')[0][len(Config.TRIGGER):]
#            cmd = msg[len(Config.TRIGGER):]
            if cmd in self.commands:
                self.commands[cmd](self, msg, channel, user)


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
