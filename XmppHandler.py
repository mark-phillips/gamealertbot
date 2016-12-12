#!/usr/bin/python
# Copyright 2009 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
from google.appengine.api import xmpp
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.webapp import xmpp_handlers

import re, string, time
logging.basicConfig(level=logging.DEBUG,)

from gamedb import Game
from userdb import User

from ytmt import Ytmt

XMPP_HELP_MSG = ("I am the game alert bot.  Use the following commands to control your game alerts."
            "\n   'add ytmt {ytmt-id}' - Register a YTMT user"
            "\n   'remove ytmt {ytmt-id}|{*ALL}' - Stop receiving alerts for one or all users."
            "\n   'add twitter {twitter-id}' - Register a twitter account and start receiving DM alerts to it (must follow gamealertbot)"
            "\n   'remove twitter {twitter-id}' - Stop receiving alerts to twitter account."
            "\n   'list users' - Get a list of all your registered users"
            "\n   'list games' - Get a list of all games for your registered users"
            "\To see all games and users being monitored go to %s")

class XmppHandler(xmpp_handlers.CommandHandler):
  """Handler class for all XMPP activity."""

  def help(self, message=None,message_subcmd=None):
    logging.debug(  "processing 'help' command" )
    printhelp = False
    message_subcmd
    if len(message.arg.split()) > 1:
        message_subcmd = message.arg.upper().strip().split()[1]
    if message_subcmd:
        if (message_subcmd == "LIST"):
            message.reply("""LIST SYNTAX:
            -  "list games" - Show all games you are participating in
            -  "list users" - Show all registered YTMT users""")
    # Show help text
    google_user = db.IM("xmpp", message.sender).address.split('/')[0]
    message.reply(XMPP_HELP_MSG % (self.request.host_url + "?ytmt_user=YTMTUSER" + ytmt_user))

  #
  #  Process incoming message
  def text_message(self, message=None):
    logging.debug(  "processing command" )
    printhelp = True
    message_subcmd = None
    message_cmd = message.arg.upper().strip().split()[0]

    if ( len(message.arg.split()) > 1):
        message_subcmd = message.arg.strip().split()[1]

    if (message_cmd == "LIST"):
        if message_subcmd:
            if (message_subcmd == "USERS"):
                self.list_users(message)
                printhelp = False
            else:
                self.list_games(message)
                printhelp = False
    elif (message_cmd == "ADD"):
        if message_subcmd:
            name = message_subcmd
            self.add_user(message,name)
            printhelp = False
    elif (message_cmd == "REMOVE"):
        if message_subcmd:
            name = message_subcmd
            self.remove_user(message,name)
            printhelp = False
    if printhelp == True:
            self.help(message)


  def list_games(self, message=None):
    logging.debug(  "processing 'list games' command" )
    #
    # List the games in the Db
    # TODO - need to limit to current user's registrations
    # google_id =  db.IM("xmpp", message.sender).address.split('/')[0]
    # users = db.GqlQuery("SELECT * FROM User WHERE google_id = :1", google_id)
    # if ( users.count() == 0  ) :
        # notification = "You haven't registered any YTMT ids.  Use the 'add' command to register an Id."
    # else:
    games_now = db.GqlQuery("SELECT * FROM Game")
    if ( games_now.count() == 0  ) :
        notification = "No games in database"
    else:
        notification = ""
        for g in games_now:
                if (g.whoseturn == g.player):
                    preamble = "It's " + g.player + "'s turn against "
                else:
                    preamble = "It's NOT " + g.player + "'s turn against "
                notification = notification + ", " + preamble + g.opponent +" in " + g.type + " game "+ g.game + " - " + g.clicklink
    message.reply(notification)

  def list_users(self, message=None):
    logging.debug(  "processing 'list users' command" )
    #
    # List the users in the Db
    google_id =  db.IM("xmpp", message.sender).address.split('/')[0]
    users = db.GqlQuery("SELECT * FROM User WHERE google_id = :1", google_id)
    if ( users.count() == 0  ) :
        notification = "You haven't registered any YTMT ids.  Use the 'add ytmt' command to register an Id."
    else:
        notification = "You are monitoring the following YTMT users: "
        twitter_id = None
        for u in users:
                notification = notification + "  " + u.ytmt_id
                if u.twitter_id != None:
                    twitter_id = u.twitter_id
        if twitter_id != None:
                notification = notification + ".  Notifications will be sent to Twitter Id:  " + twitter_id
    message.reply(notification)

  def add_user(self, message=None, name=None):
    logging.debug(  "processing 'add ytmt user' command" )
    new_user = User()
    im_from = db.IM("xmpp", message.sender)
    new_user.google_id = im_from.address.split('/')[0]
    new_user.ytmt_id = name
    new_user.put()
    logging.debug( "Added " + name + " for : " + new_user.google_id  )
    message.reply("Added user '" + name + "'.  Alerts for '" + name + "' will be sent to: " + new_user.google_id + ".")

  def remove_user(self, message=None, name=None):
    logging.debug(  "processing 'remove user' command for " + name )
    google_id =  db.IM("xmpp", message.sender).address.split('/')[0]
    users = db.GqlQuery("SELECT * FROM User WHERE google_id = :1", google_id)
    for u in users:
        if (name == "*ALL" or name == u.ytmt_id ):
            logging.debug( "Deleting " + u.ytmt_id )
            u.delete()
            #
            # TODO: REmove games here
    if (name == "*ALL"):
        message.reply("Removed all ytmt ids for :" + google_id)
    else:
        message.reply("Removed user '" + name  + "'.  No more alerts will be sent to " + google_id + " about '" + name + "'.")

