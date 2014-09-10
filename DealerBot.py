from Config import Config
from Game import Game
from Player import Player

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

# system imports
import time, sys

class MessageLogger:
    """
    An independent logger class (because separation of application
    and protocol logic is a good thing).
    """
    def __init__(self, file):
        self.file = file

    def log(self, message):
        """Write a message to the file."""
        timestamp = time.strftime("[%H:%M:%S]", time.localtime(time.time()))
        self.file.write('%s %s\n' % (timestamp, message))
        self.file.flush()

    def close(self):
        self.file.close()


class DealerBot(irc.IRCClient):
    
    nickname = "dealer"

    players = {}
    joinindex = 0

    def isPlayer(self, nick):
        for k, v in self.players.iteritems():
            if nick == v.nick:
                return True
        return False
 
    def doJoin(self, msg, channel, user):
        if self.isPlayer(user):
            self.msg(user, "You are already playing!")
        elif len(self.players) >= Config.PLAYERS_MAX:
            msg = user + ": No more than " + str(Config.PLAYERS_MAX) + " players permitted."
            self.msg(channel, msg)
        else:
            msg = user + " is attempting to join the game."
            self.msg(channel, msg)
            whois = self.whois(user)
            # hostmask = result of /whois user; hostmask = self.whois(%s)?
            # players[joinindex] = Player(hostmask, <%s>)
            # joinindex = joinindex + 1

    def doStart(self, msg, channel, user):
        # Someone attempts to start  
        if self.isPlayer(user): # Only players may start a game
            if len(self.players) < Config.PLAYERS_MIN:
                msg = user + ": Minimum of " + str(Config.PLAYERS_MIN) + " players required to start a game."
                self.msg(channel, msg)
            else:
                self.start()

    def doStats(self, msg, channel, user):
        pass    

    commands = { "j" : doJoin,
                 "join" : doJoin,
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

    # callbacks for events

    def irc_RPL_WHOISUSER(self, prefix, params):
        print params

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.join(self.factory.channel)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        self.logger.log("[I have joined %s]" % channel)

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]
        self.logger.log("<%s> %s" % (user, msg))
        
        # Check to see if they're sending me a private message
        if channel == self.nickname:
            msg = "Dealer's choice"
            self.msg(user, msg)
            return

        # Otherwise check to see if it is a message directed at me
        if msg.startswith(self.nickname + ":"):
            msg = "%s: lol" % user
            self.msg(channel, msg)
            self.logger.log("<%s> %s" % (self.nickname, msg))


        if msg.startswith(Config.TRIGGER):
            cmd = msg[len(Config.TRIGGER):]
            if cmd in self.commands:
                self.commands[cmd](self, msg, channel, user)

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        user = user.split('!', 1)[0]
        self.logger.log("* %s %s" % (user, msg))

    # irc callbacks

    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        self.logger.log("%s is now known as %s" % (old_nick, new_nick))


    # For fun, override the method that determines how a nickname is changed on
    # collisions. The default method appends an underscore.
    def alterCollidedNick(self, nickname):
        """
        Generate an altered version of a nickname that caused a collision in an
        effort to create an unused related name for subsequent registration.
        """
        return nickname + '^'

    def start(self):
        game = Game(self.players)
        game.play()


class DealerBotFactory(protocol.ClientFactory):
    """A factory for DealerBots.

    A new protocol instance will be created each time we connect to the server.
    """

    def __init__(self, channel, filename):
        self.channel = channel
        self.filename = filename

    def buildProtocol(self, addr):
        p = DealerBot()
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
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
