#!/usr/bin/python
import logging
logging.basicConfig(level=logging.DEBUG,)
from ytmt import Ytmt
from bs4 import BeautifulSoup


def main():
    oldgames = {} 
    name = "markp1999"
    s = Ytmt.ReadGamesPage_NotLoggedIn( name ) 
    #logging.debug( BeautifulSoup(s).prettify()  )
    games = Ytmt.FindGamesinPage_NotLoggedIn( name, True, s) + Ytmt.FindGamesinPage_NotLoggedIn( name, False, s)

    if (games != {}):
        print "\n================================================="
        for g in games:   # Go through the list of games
            #
            # Send a notification
            if (g.whoseturn== g.player):
                preamble = g.player + " it's your turn against "
            else:
                preamble = g.player + " it's NOT your turn against "
                
            notification =  preamble + g.opponent +" in " + g.type + " game "+ g.id + "\n" + g.clicklink 
            print notification

    else:
        print "No games to play"
   
    print "================================================="

   
   

if __name__ == '__main__':
  main()
