from google.appengine.ext import db
class twitter_auth(db.Model):
    "Twitter Credentials"
    API_key = db.StringProperty()
    API_secret = db.StringProperty()
    Access_token = db.StringProperty()
    Access_token_secret = db.StringProperty()
    last_status_id = db.IntegerProperty()
#    last_dm_id = db.IntegerProperty()
