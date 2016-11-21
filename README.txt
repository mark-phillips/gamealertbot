In Bash

To upload...

cd /m/IBMUSB/Documents/projects/Python/
cd ytmt/
appcfg.py update ../src/ytmt

ON WINDOWS
===========
run...
"C:\Program Files (x86)\Google\google_appengine\appengine_launcher.bat"

python C:\ProgramFilesx86\Google\google_appengine\appcfg.py update ..\ytmt

=======================================================================

Project Structure
=================

bot.py - Logic for responding to requests
ytmt.py - Scraping ytmt site
game.py - abstract class containing game details
notifier.py - send xmpp notifications

gamedb.py - db model class
userdb.py - db model class

web.py - Serving web pages
