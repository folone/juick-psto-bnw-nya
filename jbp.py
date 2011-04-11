from google.appengine.api import xmpp
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app

import logging

HELP_MSG = """Hello. I can post to juick and psto simultaneously. To start:
  1. Send me \"register <nickname>\" command with your desired nickname instead of <nickname>.
  2. I will respond with a JID, that you should add to your accounts.
     For juick use this link: http://juick.com/settings, for psto -- this one: http://folone.psto.net/profile/accounts.
  3. Juick will ask to confirm your JID. Send me \"-j AUTH <auth_code>\" command with your auth code.
  4. ...
  5. PROFIT!
  
  Now whenever you want to post to both juick and psto, just send your post to me, I'll do that for you.
  PM your requests to @folone
  More info at http://about.folone.info/projects/juickpsto"""

JUICK_BOT = "juick@juick.com"
PSTO_BOT = "psto@psto.net"
PSTO_ANOTHER_BOT = "arts@psto.net"
#BNW_BOT = "bnw@bnw.im"
#NYA_BOT = "nyashaj@neko.im

class User(db.Model):
    local = db.StringProperty(required=True)
    jid = db.StringProperty(required=True)
  
class XMPPHandler(webapp.RequestHandler):
  
    def post(self):
        message = xmpp.Message(self.request.POST)
        
        mesFrom = message.sender.split('/')[0]
        mesTo = message.to.split('/')[0]
        mesBody = message.body
        
	if mesFrom.lower() != PSTO_BOT.lower() and mesFrom.lower() != JUICK_BOT.lower() and mesFrom.lower() != PSTO_ANOTHER_BOT.lower() : # and mesFrom.lower() != BNW_BOT.lower() and mesFrom.lower() != NYA_BOT.lower() :
	  self.parseMessageFromJid(message, mesFrom)
	else :
	  self.parseMessageFromBot(message, mesFrom)
        
    def parseMessageFromJid(self, message, mesFrom) :
        user = User.all().filter(' jid', mesFrom.lower().strip()).get()
        if user is None :
	  if message.body.strip().lower().find("register") != 0 :
	    message.reply(HELP_MSG)
	  elif message.body.strip().lower().find("register") == 0 :
	    uname = message.body.strip().replace("register ", "", 1).replace(" ", "") + "@juick-bnw-psto.appspotchat.com"
	    user = db.GqlQuery("SELECT * FROM User " +
                "WHERE local = :1", uname).get()
            if user is None :
	      user = User(jid=mesFrom,local=uname)
	      user.put()
	      message.reply("Ok. Now add " + uname + " as your secondary jid to all desired services (only juick and psto for now).")
	    else :
	      message.reply("Login already taken. Choose another.")
	else :
	  # User registered, proceed
	  if message.body.strip().lower() == "help" :
	    message.reply(HELP_MSG)
	  else :
	    self.send_to_bots(message, user.local)
	  
    def parseMessageFromBot(self, message, mesFrom) :
	jid = mesFrom
	mesText = message.body.strip()
	if mesFrom.lower() == JUICK_BOT.lower() or mesFrom.lower() == PSTO_BOT.lower() or mesFrom.lower() != PSTO_ANOTHER_BOT.lower() : # or mesFrom.lower() == BNW_BOT.lower() or mesFrom.lower() == NYA_BOT.lower() :
	  # Send it to user.
	  mesTo = message.to.split('/')[0]
	  user = User.all().filter('local', mesTo.lower().lower()).get()
	  if user is None :
	    logging.debug("We've got unknown message: " + mesFrom + "->" + mesTo + ">" + mesText)
	  else :
	    from UserString import MutableString
	    mesFooter = MutableString()
	    mesFooter += "\nTo reply to this message, start your message with "
	    if mesFrom.lower() == JUICK_BOT.lower() :
	      mesFooter += "-j"
	    else :
	      mesFooter += "-p"
	    mesFooter += " modificator.\nIf you fail to do so, your message will be sent to both juick and psto."
	    status = xmpp.send_message(user.jid, mesFrom + "> " + (mesText + mesFooter).decode('UTF-8'))
	else :
	  # Logging.
	  logging.debug("We've got unknown message: " + mesFrom + "> " + mesText)
	  
    def send_to_bots(self, message, mesFrom) :
        mesText = message.body.strip()
        if mesText.find("-j") == 0 :
	  # Sending to juick only
	  mesText = mesText.replace("-j ", "", 1)
	  juick_status = xmpp.send_message(JUICK_BOT, mesText, mesFrom)
	  message.reply("Sent to juick succesfully: " + str(juick_status == xmpp.NO_ERROR))
	elif mesText.find("-p") == 0 :
	  # Sending to psto only
	  mesText = mesText.replace("-p ", "", 1)
	  psto_status = xmpp.send_message(PSTO_BOT, mesText, mesFrom)
	  message.reply("Sent to psto succesfully: " + str(psto_status == xmpp.NO_ERROR))
	#elif mesText.find("-b") == 0 :
	  # Sending to bnw only.
	  #mesText = mesText.replace("-b ", "", 1)
	  #bnw_status = xmpp.send_message(BNW_BOT, mesText, mesFrom)
	  #message.reply("Sent to bnw succesfully: " + str(bnw_status == xmpp.NO_ERROR))
	#elif mesText.find("-n") == 0 :
	  # Sending to nya only.
	  #mesText = mesText.replace("-n ", "", 1)
	  #nya_status = xmpp.send_message(NYA_BOT, mesText, mesFrom)
	  #message.reply("Sent to nya succesfully: " + str(nya_status == xmpp.NO_ERROR))
	else :
	  # Sending to all.
	  juick_status = xmpp.send_message(JUICK_BOT, mesText, mesFrom)
	  psto_status = xmpp.send_message(PSTO_BOT, mesText, mesFrom)
	  #bnw_status = xmpp.send_message(BNW_BOT, mesText, mesFrom)
	  #nya_status = xmpp.send_message(NYA_BOT, mesText, mesFrom)

	  message.reply("Sent to juick succesfully: " + str(juick_status == xmpp.NO_ERROR))
	  message.reply("Sent to psto succesfully: " + str(psto_status == xmpp.NO_ERROR))
	  #message.reply("Sent to bnw succesfully: " + str(bnw_status == xmpp.NO_ERROR))
	  #message.reply("Sent to nya succesfully: " + str(nya_status == xmpp.NO_ERROR))

application = webapp.WSGIApplication([('/_ah/xmpp/message/chat/', XMPPHandler)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
