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
                   "league":"",
                   "tab":"",
                   "color_weapons":"#457dff",
                   "color_weapons_rgb":"[200, 200, 20, 255]",
                   "color_helmets":"#457dff",
                   "color_helmets_rgb":"[200, 200, 20, 255]",
                   "color_gloves":"#457dff",
                   "color_gloves_rgb":"[200, 200, 20, 255]",
                   "color_rings":"#457dff",
                   "color_rings_rgb":"[200, 200, 20, 255]",
                   "color_amulets":"#457dff",
                   "color_amulets_rgb":"[200, 200, 20, 255]",
                   "color_bodies":"#457dff",
                   "color_bodies_rgb":"[200, 200, 20, 255]",
                   "color_boots":"#457dff",
                   "color_boots_rgb":"[200, 200, 20, 255]",

                   
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