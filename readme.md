# MizaBOT  
* /gbfg/ Discord Bot  
#### Requirements  
* Python 3.7.  
* Just do `pip install -r requirements.txt` to install the modules.  
### Usage  
* It's designed to be used on Heroku.  
* Just do a git push to your Heroku app but don't expect it to work right away:  
* You need to setup a config.json with your twitter & discord tokens, and more.  
* You also need a save.json file  
* You probably need to rewrite some checks related to the (You) Server.  
* If you just want an invite for the "official" one, ask the author.  
### Update note  
* 2.6+: the bot load and save his data in a google drive folder, which require google api credentials and more annoying stuff to setup...  
* 3.6+: the tweepy module used by the `twitter` command has been removed.  
* 4.0: Old commits have been removed for security reasons.  