from google.appengine.ext import db

class Game(db.Model):
    "Details of a Game"
    game = db.StringProperty()
    clicklink = db.StringProperty()
    type = db.StringProperty()
    player = db.StringProperty()
    opponent = db.StringProperty()
    whoseturn = db.StringProperty()
