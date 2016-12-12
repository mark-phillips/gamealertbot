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
import logging, datetime
logging.basicConfig(level=logging.DEBUG,)

from twitterdb import twitter_auth
from google.appengine.ext import db
from google.appengine.ext import webapp
import logging, tweepy
from userdb import User


################################################################
#  Check for twitter mentions and reply                        #
################################################################
class TwitterHandler(webapp.RequestHandler):

    def twitter_login(self):
        credential = twitter_auth.get_by_key_name ("apikey")
        if credential != None:
            auth = tweepy.OAuthHandler(credential.API_key, credential.API_secret)
            auth.set_access_token(credential.Access_token , credential.Access_token_secret )
            return tweepy.API(auth)

    def twid(self, ):
        """Get a minute to make tweet unique"""
        today = datetime.date.today()
        y = today.year
        prefix = y - 1967
        m = today.month
        if  m > 6 or (m == 6 and datetime.date.day >= 5 ):
            prefix = prefix+1
            y = y+1
        return str(prefix) + str(int(( datetime.datetime.now()-datetime.datetime(y,6,5)).total_seconds())/60)

    def dm(self, target, message):
            api = self.twitter_login()
            logging.debug( 'dm to:' + target + " Message:" + message)
            try:
                api.send_direct_message(target, text=message)
            except tweepy.TweepError as e :
                logging.warning( 'Error: Failed to send DM to ' + target+ ". Message: " + message)
                logging.warning( e)

    def tweet(self, target, message, reply_to=None):
            api = self.twitter_login()
            minutes = self.twid()
            logging.debug( 'Tweet to:' + target + " Message:" + message + " " + minutes)
            try:
                api.update_status("@" + target + " " + message  + " " + minutes,in_reply_to_status_id=reply_to)
            except tweepy.TweepError as e :
                logging.warning( 'Error: Failed to tweet to ' + target+ ". Message: " + message)
                logging.warning( e)

    def save_id(self,id):
        """Save last status ID to a file"""
        twitter = twitter_auth.get_by_key_name ("apikey")
        twitter.last_status_id = id
        twitter.put()
        logging.debug( "Updated last id to  " + str(id) + "."  )

    def save_dm_id(self,dmid):
        """Save last status ID to a file"""
        twitter = twitter_auth.get_by_key_name ("apikey")
        twitter.last_dm_id = dmid
        twitter.put()
        logging.debug( "Updated last dmid to  " + str(id) + "."  )

    def get_last_id(self):
        """Retrieve last status ID from a file"""
        twitter = twitter_auth.get_by_key_name ("apikey")
        #if twitter.last_status_id != None:
        #        logging.debug( "Got last id " + str(twitter.last_status_id) + "."  )
        return twitter

    def respond_to_mention(self, mention):
        """respond_to_mention"""
        twittername = mention.user.screen_name.lower()
        message = mention.text
        logging.debug(  "processing command " + message)
        message_subcmd = None
        message_cmd = message.upper().strip().split()[1]
        if ( len(message.split()) > 2):
            message_subcmd = message.strip().split()[2]

        if (message_cmd == "ADD"):
            reply = self.add_user(twittername,message_subcmd)
        elif (message_cmd == "REMOVE"):
            reply = self.remove_user(twittername,message_subcmd)
        else:
            reply = "Request not understood. Syntax: add {ytmt-user} or remove {ytmt-user} (add text to make tweet unique if required)"
        self.tweet(twittername, reply, mention.id)

    def add_user(self, twittername, name):
        logging.debug(  "processing 'add user' command" )
        if name:
            new_user = User()
            new_user.twitter_id = twittername
            new_user.ytmt_id = name
            new_user.put()
            logging.debug( "Added " + name + " for : " + twittername )
            reply = "You will receive alerts when it is " + name + "'s turn on YTMT. Tweet \"remove " + name + "\" to stop."
            #api = self.twitter_login()
            #api.create_friendship(twittername)           
        else:
            reply = "No name given for add request - syntax: add {ytmt-user}"
        return reply

    def remove_user(self, twittername, name):
        logging.debug(  "processing 'remove user' command" )
        users = db.GqlQuery("SELECT * FROM User WHERE twitter_id = :1", twittername)
        if name:
            reply = "No entry found for " + name + ". No action taken."
            for u in users:
                if u.ytmt_id == name:
                    logging.debug( "Removed record.  twitter_id: " + u.twitter_id + " ytmt_id: " + u.ytmt_id  )
                    u.delete()
                    reply = name + " removed.  You will no longer receive alerts when it is " + name + "'s turn on YTMT."
                    #api = self.twitter_login()
                    #api.destroy_friendship(twittername)           
        else:
            reply = "No name given for remove request - syntax: remove {ytmt-user}"
        return reply


    def get(self):
        """Get recent mentions."""
        twitter_ids = self.get_last_id()

        api = self.twitter_login()
        mymentions = api.mentions_timeline(since_id=twitter_ids.last_status_id)
        mydms = api.direct_messages(since_id=twitter_ids.last_dm_id)
        # want these in ascending order, api orders them descending
        mymentions.reverse()
        mydms.reverse()

        self.response.out.write('<html><body>')
        self.response.out.write('<h1>Tweets</h1>')
        if mymentions == None or len(mymentions) == 0:
            self.response.out.write('No mentions.')
        if mydms == None or len(mydms) == 0:
            self.response.out.write('No direct messages.')
        if mydms != None or mymentions != None:
            self.response.out.write( "<ul>" )
            for mention in mymentions:
                self.response.out.write( "<li>tweet from @" + mention.user.screen_name.lower() + " text: \"" + mention.text + "\", id: " + str(mention.id) )
                self.respond_to_mention(mention)
                self.save_id(mention.id)
            for dm in mydms:
                self.response.out.write( "<li>dm from @" + dm.sender.screen_name.lower() + " text: \"" + dm.text + "\", id: " + str(dm.id) )
#                self.respond_to_mention(mention)
                self.save_dm_id(dm.id)
            self.response.out.write( "</ul>" )
        self.response.out.write( "<hr>" )
        self.response.out.write(   "</body></html>"   )
