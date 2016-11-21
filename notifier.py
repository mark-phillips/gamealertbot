
from google.appengine.api import xmpp
import logging

class Notifier():
    """Notify by sending IM."""
    def notify(self,address,message):
        xmpp.send_message(address, message)

