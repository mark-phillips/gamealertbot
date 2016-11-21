from google.appengine.ext import db
class User(db.Model):
    "Details of a User"
    google_id = db.StringProperty()
    ytmt_id = db.StringProperty()
    twitter_id = db.StringProperty()
