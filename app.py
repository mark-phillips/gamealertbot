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
import datetime
import logging
import os
import wsgiref.handlers
from google.appengine.api import xmpp
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.ereporter import report_generator
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import xmpp_handlers

import re, string, time
logging.basicConfig(level=logging.DEBUG,)

from bot import *
from TwitterHandler import *
from gamedb import Game
from userdb import User
from twitterdb import twitter_auth

from ytmt import Ytmt
from notifier import Notifier


# Save away the old games list to a dictionary
def copy_gamesDb_to_dict_and_purge(player, currentgames):
    old_dict = {}
    oldgames = db.GqlQuery("SELECT * FROM Game  WHERE player = :1", player)
    for g in oldgames:
        old_dict[g.game] = g
        #
        # Purge games from the database where it's not your turn any more
        if (len(currentgames) == 0 or currentgames.has_key(g.game) == False):
            g.delete()
            logging.debug(  "cleared game " + g.game + " " + player)
    return old_dict


#
# Save away the game
def save_game(g):
    this_game = Game(key_name=g.game)
    this_game.player = g.player
    this_game.opponent = g.opponent
    this_game.game = g.game
    this_game.type = g.type
    this_game.clicklink= g.clicklink
    this_game.whoseturn= g.whoseturn
    this_game.put()

def setup_twitter_auth():
    twitter_auth.get_or_insert("apikey",API_key="XXXXXXXXXXXXXXXXXXXXXXXXX",  \
        API_secret = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", \
        Access_token = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", \
        Access_token_secret = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"   )


################################################################
#  Build up Web page with full list of games and alert users   #
################################################################
class RootHandler(webapp.RequestHandler):

    """Displays a list of games message."""
    def get(self):
        setup_twitter_auth()

        self.response.out.write('<html><body>')
        ytmt_user = self.request.get("ytmt_user")
        if ( ytmt_user != "" ) :
            self.response.out.write( "<h1>Alerts for User " + ytmt_user + "</h1>" )
            users = db.GqlQuery("SELECT * FROM User WHERE ytmt_id = :1", ytmt_user)
        else :
            #
            # Forget the current list of games in a web document for all users
            users = db.GqlQuery("SELECT * FROM User")

        #
        # Handle case of no users being registered
        if ( users.count() == 0  ) :
            logging.debug(  "No users registered " )
            self.response.out.write( "<h2>No Users Registered</h2>" )
            self.response.out.write( "To register YTMT ids, use google talk to connect to gamealertbot@appspot.com ")
            self.response.out.write( "or twitter to follow @gameealertbot ")
            self.response.out.write("then use the 'add {ytmt_id}' command to register your YTMT id.")
        #
        # Or handle each registered user
        else:
            for u in users:
                logging.debug(  "Processing " + u.ytmt_id)
                name = u.ytmt_id
                google_id = u.google_id
                self.response.out.write( "<h2>" + name + "'s turn </h2>")
                if google_id != None:
                    self.response.out.write( "<h3>(xmpp alerts to " +  google_id+ ")</h3>")
                twitter_id = u.twitter_id
                if twitter_id != None:
                    self.response.out.write( "<h3>(tweets to " +  twitter_id+ ")</h3>")
                #twitter_dm_id = u.twitter_dm_id
                #if twitter_dm_id != None:
                #    self.response.out.write( "<h3>(twitter dms to " +  twitter_id+ ")</h3>")

                #
                # Download the user's overview page
                s = Ytmt.ReadGamesPage_NotLoggedIn( name )
                if ( s != None ):

                    #
                    #
                    # First parse out games where it is your turn
                    games = Ytmt.FindGamesinPage_YourTurn( name, s)
                    #
                    # Save away the old "your turn" games list for this user to
                    # a dictionary and clear the database
                    old_dict = copy_gamesDb_to_dict_and_purge(name, games)
                    if (len(games) == 0):
                        self.response.out.write( "(No games)"  )
                    else:
                        self.response.out.write( "<hr>" )
                        self.response.out.write( "<ul>" )

                        for key in games:
                            g = games[key]
                            #
                            # Compare the old and new games list
                            # TODO: do this by querying the database & do away with dictionary
                            # If this is an old game and it was your turn last time then just print it - dont send IM
                            game_details = g.opponent +" in " + g.type + " game <a href=\"" + g.clicklink + "\">"+ g.game  + "</a>"
                            IM_game_details = g.opponent +" in " + g.type + " game "+ g.clicklink
                            TW_game_details = g.opponent +" in " + g.type + " game "+ g.game
                            if ( old_dict.has_key(g.game) == True and old_dict[g.game].whoseturn == g.player):
                                notification =  g.player + " still your turn against " + game_details
                                self.response.out.write( "<li>" + notification )
                            else:
                            # Else, new game or newly your turn - send the notification and save the game
                                logging.debug(  "saved game " + g.game + " " + name)
                                notification =  g.player + " it's your turn against "
                                self.response.out.write( "<li><b>" + notification + game_details + "</b>")
                                if google_id != None:
                                    Notifier().notify(google_id, notification +IM_game_details)
                                if twitter_id != None:
                                    TwitterHandler().tweet(twitter_id, ":" + g.player + "'s turn against" + IM_game_details )
                                #if twitter_dm_id != None:
                                #    Notifier().dm(twitter_id, notification +TW_game_details )
                                logging.debug(  "Notifying google_id: " + notification + game_details)
                                save_game(g) # write game to database

                        self.response.out.write( "</ul>" )
                        self.response.out.write( "<hr>" )
                    #
                    # Now list games where it's not your turn
                    self.response.out.write( "<h2>" + name + "'s Opponent's Turn</h2>")
                    #
                    # List games where it's not your turn
                    games = Ytmt.FindGamesinPage_OpponentsTurn( name, s)
                    if (len(games) == 0):
                        self.response.out.write( "(No games)"  )
                    else:
                        self.response.out.write( "<ul>" )
                        for key in games:
                            g = games[key]
                            g.clicklink = g.clicklink.replace(" ", "+")
                            game_details = g.player +" in " + g.type + " game <a href=\"" + g.clicklink + "\">"+ g.game  + "</a>"
                            notification =  g.opponent + "'s turn against " + game_details
                            self.response.out.write( "<li>" + notification )

                        self.response.out.write( "</ul>" )
                    self.response.out.write( "<hr>" )

                else:
                    self.response.out.write( "No games to play or web access failed")


        self.response.out.write(   "</body></html>"   )


def main():
  app = webapp.WSGIApplication([
      ('/twitter', TwitterHandler),
      ('/', RootHandler),
      ('/_ah/xmpp/message/chat/', XmppHandler),
      ], debug=True)
  wsgiref.handlers.CGIHandler().run(app)

if __name__ == '__main__':
  main()
