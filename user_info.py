# import private
import configparser

def save():
    with open(CFG_FILENAME,"w") as config_file:
        cfg.write(config_file)

def load():
    cfg.read(CFG_FILENAME)

# CFG info
CFG_FILENAME = r"user_settings.cfg"
cfg = configparser.ConfigParser()

# load base info
load()
# REDIRECT_URI = cfg["api"]["REDIRECT_URI"]
# CLIENT_ID = cfg["api"]["CLIENT_ID"]
# CLIENT_SECRET = cfg["api"]['CLIENT_SECRET']
# SCOPE = cfg["api"]["SCOPE"]
# DEV_TOKEN = cfg["api"]["DEV_TOKEN"]
