#!/usr/bin/python
import urllib2
import logging
import time
from bs4 import BeautifulSoup
from game import Game

HOME_PAGE = "http://www.yourturnmyturn.com/index.php"
PROFILE_INFORMATION_PREFIX = "http://www.yourturnmyturn.com/user.php?username="
PROFILE_INFORMATION_SUFFIX  = "&toonbeurt=1"

class Ytmt():

    ########################################################################
    #   Read anyone's page from web
    ########################################################################
    @staticmethod
    def ReadGamesPage_NotLoggedIn (name) :
        s = None
        handle = None
        try:
            logging.debug( """Fetching At:  %02d:%02d""" % (time.localtime()[3], time.localtime()[4] ))
            url = PROFILE_INFORMATION_PREFIX + name + PROFILE_INFORMATION_SUFFIX
            response = urllib2.urlopen(url)
            s = response.read()
            logging.debug(  "Finished" )
            #logging.debug( s )
            return s

        except:
            logging.debug(  """COMMS ERROR At:  %02d:%02d""" % (time.localtime()[3], time.localtime()[4] ) )
            return None

    ########################################################################
    #   Parse games page to get a list of games
    ########################################################################
    @staticmethod
    def FindGamesinPage_NotLoggedIn (name, isItYourTurn, page) :
        games = {}
        #
        #  Get Table Rows
        soup = BeautifulSoup(page)
        #
        #  Whose turn are we looking for?
        if isItYourTurn:
            Turn= "Turn " + name
        else:
            Turn= "Opponent's turn " + name
        #
        # Find the appropriate table
        txt = soup.find(text=Turn)
        #
        # Bomb out if no data found for user
        if (txt) :
            table = txt.findPrevious('table')
        else:
            return []
        #logging.debug( table.prettify() )
        for row in table.findAll('tr',recursive=True):
            #logging.debug( row )
            column = row.findAll('td',recursive=False)
            if (column[0]):
                #
                # Ignore the row if it doesn't have > 2 columns
                if (len(column) > 2):
                    this_game = Game()

                    opponent = column[0].contents[0][2:] # Name starts in 2nd character
                    if (column[1].a) :
                        type = unicode(column[1].contents[1] ).strip() # Skip the hyperlink if found
                    else:
                        type = unicode(column[1].contents[0] ).strip()  # or use contents
                    relpath = column[2].a['href']
                    number = relpath.split("gamenumber=")[1]
                    link = "http://www.yourturnmyturn.com/" + type + "/play.php?gamenumber=" + number
                    link = link.replace(" ", "+")

                    this_game.player=name
                    this_game.opponent=opponent
                    this_game.game = number
                    this_game.type = type
                    this_game.clicklink=link
                    if isItYourTurn:
                        this_game.whoseturn=name
                    else:
                        this_game.whoseturn=opponent
                    games[this_game.game] = this_game

        return games


    ########################################################################
    #   Parse games page to get a list of games where it is the users turn
    ########################################################################
    @staticmethod
    def FindGamesinPage_YourTurn (name, page) :
        return Ytmt.FindGamesinPage_NotLoggedIn (name, True, page)

    ########################################################################
    #   Parse games page to get a list of games where it is opponents turn
    ########################################################################
    @staticmethod
    def FindGamesinPage_OpponentsTurn (name, page) :
        return Ytmt.FindGamesinPage_NotLoggedIn (name, False, page)


