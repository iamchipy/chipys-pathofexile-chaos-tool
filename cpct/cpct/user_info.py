# import private
import configparser
import os

# const
BASE_RGB = "0, 255, 255"
CFG_FILENAME = r"user_settings.cfg"
# CFG info
cfg = configparser.ConfigParser()

def save():
    with open(CFG_FILENAME,"w") as config_file:
        cfg.write(config_file)

def load():
    # Set deafults
    cfg["form"] = {"filter_dir": os.path.expanduser("~/Documents")+"/My Games/Path of Exile/",
                   "filter_name":"Browse To Select",
                   "client_path":"Browse To Select",
                   "username":"",
                   "league":"standard",
                   "tab":"1",
                   "sets_goal":"4",
                #    "color_weapon":"#00ffff",
                   "color_weapon_rgba":"["+BASE_RGB+", 235]",
                #    "color_helmet":"#00ffff",
                   "color_helmet_rgba":"["+BASE_RGB+", 210]",
                #    "color_gloves":"#00ffff",
                   "color_gloves_rgba":"["+BASE_RGB+", 210]",
                #    "color_ring":"#00ffff",
                   "color_ring_rgba":"["+BASE_RGB+", 255]",
                #    "color_amulet":"#00ffff",
                   "color_amulet_rgba":"["+BASE_RGB+", 255]",
                #    "color_body_armour":"#00ffff",
                   "color_body_armour_rgba":"["+BASE_RGB+", 150]",
                #    "color_boots":"#00ffff",
                   "color_boots_rgba":"["+BASE_RGB+", 210]",
                #    "color_belt":"#00ffff",
                   "color_belt_rgba":"["+BASE_RGB+", 235]",                   
                   }


    cfg["api"] = {"CLIENT_ID":"chipytools",
                  "CLIENT_SECRET":"AskChipyForThis",
                  "SCOPE":"account:profile account:characters account:stashes account:item_filter",
                  "REDIRECT_URI":"https://chipy.dev/poe_auth.html",
                  "TOKEN":"",
                  }
    cfg.read(CFG_FILENAME)

def get(section:str, key:str):
    result = cfg.get(section, key, fallback="MISSING")
    if "[" in result:
        return result[1:-1].split(",")
    return result

def set(section:str, key:str, value:str):
    cfg[section][key] = value
    save()

if __name__ == "__main__":
    load()
    print(type(get("form","color_amulet_rgb")))
    print(get("form","color_amulet_rgb"))