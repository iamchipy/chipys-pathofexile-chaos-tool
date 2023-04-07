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
                   "color_weapon":"#ff00ff",
                   "color_weapon_rgb":"[255, 0, 255, 255]",
                   "color_helmet":"#ff00ff",
                   "color_helmet_rgb":"[255, 0, 255, 255]",
                   "color_gloves":"#ff00ff",
                   "color_gloves_rgb":"[255, 0, 255, 255]",
                   "color_ring":"#ff00ff",
                   "color_ring_rgb":"[255, 0, 255, 255]",
                   "color_amulet":"#ff00ff",
                   "color_amulet_rgb":"[255, 0, 255, 255]",
                   "color_body_armour":"#ff00ff",
                   "color_body_armour_rgb":"[255, 0, 255, 255]",
                   "color_boot":"#ff00ff",
                   "color_boot_rgb":"[255, 0, 255, 255]",
                   "color_belt":"#ff00ff",
                   "color_belt_rgb":"[255, 0, 255, 255]",                   
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