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
