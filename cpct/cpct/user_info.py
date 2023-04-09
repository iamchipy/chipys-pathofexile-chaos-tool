# import private
import configparser
import os

# const
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
                   "color_weapon":"#00ffff",
                   "color_weapon_rgb":"[0, 255, 255, 235]",
                   "color_helmet":"#00ffff",
                   "color_helmet_rgb":"[0, 255, 255, 210]",
                   "color_gloves":"#00ffff",
                   "color_gloves_rgb":"[0, 255, 255, 210]",
                   "color_ring":"#00ffff",
                   "color_ring_rgb":"[0, 255, 255, 255]",
                   "color_amulet":"#00ffff",
                   "color_amulet_rgb":"[0, 255, 255, 255]",
                   "color_body_armour":"#00ffff",
                   "color_body_armour_rgb":"[0, 255, 255, 150]",
                   "color_boots":"#00ffff",
                   "color_boots_rgb":"[0, 255, 255, 210]",
                   "color_belt":"#00ffff",
                   "color_belt_rgb":"[0, 255, 255, 235]",                   
                   }


    cfg["api"] = {"CLIENT_ID":"chipytools",
                  "CLIENT_SECRET":"AskChipyForThis",
                  "SCOPE":"account:profile account:characters account:stashes account:item_filter",
                  "REDIRECT_URI":"https://chipy.dev/poe_auth.html",
                  "TOKEN":"",
                  }
    cfg.read(CFG_FILENAME)

def get(section:str, key:str) -> str:
    return cfg.get(section, key, fallback="MISSING")

def set(section:str, key:str, value:str):
    cfg[section][key] = value
    save()

if __name__ == "__main__":
    print(get("api","client_id"))
    load()
    print(get("api","client_id"))
    save()