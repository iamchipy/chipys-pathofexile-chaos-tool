import typing
import datetime
import os
import sys
import time
import webbrowser
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QApplication, QColorDialog, QInputDialog, QWidget
from PyQt5 import QtGui
from PyQt5.QtCore import QTimer, Qt
import qt.main_gui
import ctypes
import poepy
import user_info
from __about__ import __version__
import logging

# PoE dev Docs for ref
# https://www.pathofexile.com/developer/docs
# TYPE/Structures
# https://www.pathofexile.com/developer/docs/reference#type-Item

# type checking block (AND RUFF INFO)
# https://www.youtube.com/watch?v=bcAqceZkZRQ
if typing.TYPE_CHECKING:
    api:poepy.PoeApiHandler
    parser:poepy.DataParser
    gui:qt.main_gui.MainWindow

# set statics
IMG_FOLDER = os.path.realpath(__file__)[:-7]+"img\\"
ASYNC_INTERVAL_MS = 1000
PROGRESS_BAR_STYLE = """
QProgressBar {
	text-align: center;
	border-radius: 8px;
}
QProgressBar::chunk {
	background-color: #05B8CC;
	border-radius: 6px;
}
"""

# variables for searching log files to detect new zone
modified = 0
async_time = time.time()
previous = 0
zone_log = []
filter_updated = False
slot_count = None
refresh_off_cooldown = True
recipe_handler = None

class AsyncMainWindow(QMainWindow):
    log_timer = QTimer()
    def __init__(self):
        super().__init__()
        self.init_async()

    def init_async(self):
        print("Initializing . . . ", end="")
        self.log_timer.timeout.connect(async_two)
        self.log_timer.start(ASYNC_INTERVAL_MS)
        print("Started")

def p_l(*args):
    ts = timestamp()
    print(*args)
    logging.warn(ts+str(*args))

def timestamp():
    return time.strftime("%H:%M:%S")

def try_wrapper(function):
    """Simple wrapper that includes a TRY loop
    Args:
        function (Func): Returns the provided function wrapped Try
    """
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as e:
            p_l(timestamp(), function.__name__, "=> FAILED:", e)
            return False
    return wrapper  

def timed_try_wrapper(function):
    """Simple timing wrapper that also includes a TRY loop
    Args:
        function (Func): Returns the provided function wrapped with Time and Try
    """
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = function(*args, **kwargs)
            end = time.time()
            print(function.__name__, "=> RunTime:",end-start)
            return result
        except Exception as e:
            end = time.time()
            print(timestamp(), function.__name__, "=> FAILED:",end-start, e)
            result = False
    return wrapper    

def apply_ui_defaults(gui_obj, window_obj, app_obj):

    # set window Icons
    app_obj.setWindowIcon(QtGui.QIcon(IMG_FOLDER+'cpct_logo.png'))
    window_obj.setWindowTitle(f"Chipy's PoE Chaos Tool (v{__version__})")
    
    # set login icon (this is to fix the image path issue)
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(IMG_FOLDER+"poe.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    gui_obj.login_link.setIcon(icon)
    print(IMG_FOLDER+"dropper.png")
    icon.addPixmap(QtGui.QPixmap(IMG_FOLDER+"dropper.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    gui_obj.color_link_rings.setIcon(icon)
    gui_obj.color_link_amulets.setIcon(icon)
    gui_obj.color_link_belts.setIcon(icon)
    gui_obj.color_link_bodies.setIcon(icon)
    gui_obj.color_link_boots.setIcon(icon)
    gui_obj.color_link_helmets.setIcon(icon)
    gui_obj.color_link_weapons.setIcon(icon)
    gui_obj.color_link_gloves.setIcon(icon)

    # set previous selections
    gui_obj.item_filter_browse.setText(os.path.split(user_info.get("form", "filter_name"))[1])
    gui_obj.client_secret_input.setText(user_info.get("api","client_secret"))
    gui_obj.client_path_browse.setText(user_info.get("form", "client_path")[0:22]+"..."+user_info.get("form", "client_path")[-13:])
    gui_obj.sets_target.setValue(int(user_info.get("form", "sets_goal")))

    # set previous colours
    gui_obj.count_amulets.setStyleSheet(style_sheet_new_color(PROGRESS_BAR_STYLE, user_info.get("form", "color_amulet_rgba")))
    gui_obj.count_belts.setStyleSheet(style_sheet_new_color(PROGRESS_BAR_STYLE, user_info.get("form", "color_belt_rgba")))
    gui_obj.count_bodies.setStyleSheet(style_sheet_new_color(PROGRESS_BAR_STYLE, user_info.get("form", "color_body_armour_rgba")))
    gui_obj.count_boots.setStyleSheet(style_sheet_new_color(PROGRESS_BAR_STYLE, user_info.get("form", "color_boots_rgba")))
    gui_obj.count_gloves.setStyleSheet(style_sheet_new_color(PROGRESS_BAR_STYLE, user_info.get("form", "color_gloves_rgba")))
    gui_obj.count_helmets.setStyleSheet(style_sheet_new_color(PROGRESS_BAR_STYLE, user_info.get("form", "color_helmet_rgba")))
    gui_obj.count_rings.setStyleSheet(style_sheet_new_color(PROGRESS_BAR_STYLE, user_info.get("form", "color_ring_rgba")))
    gui_obj.count_weapons.setStyleSheet(style_sheet_new_color(PROGRESS_BAR_STYLE, user_info.get("form", "color_weapon_rgba")))

    # defaults for item_filter modes
    gui_obj.filter_mode.addItems(["Default","FilterBlade","Custom","Disabled"])
    
def apply_ui_connections(gui_obj, parser):
    """Overlay that connects up the GUI so that we can modularly replace the gui.py from QT5
    https://www.geeksforgeeks.org/function-wrappers-in-python/
    Args:
        gui_obj (gui.Ui_MainWindow): Main window GUI object
    """
    # Link ColorPickers
    gui_obj.color_link_amulets.clicked.connect(lambda: pick_color(gui_obj, gui_obj.count_amulets, "color_amulet_rgba"))
    gui_obj.color_link_belts.clicked.connect(lambda: pick_color(gui_obj, gui_obj.count_belts, "color_belt_rgba"))
    gui_obj.color_link_bodies.clicked.connect(lambda: pick_color(gui_obj, gui_obj.count_bodies, "color_body_armour_rgba"))
    gui_obj.color_link_boots.clicked.connect(lambda: pick_color(gui_obj, gui_obj.count_boots, "color_boots_rgba"))
    gui_obj.color_link_gloves.clicked.connect(lambda: pick_color(gui_obj, gui_obj.count_gloves, "color_gloves_rgba"))
    gui_obj.color_link_helmets.clicked.connect(lambda: pick_color(gui_obj, gui_obj.count_helmets, "color_helmet_rgba"))
    gui_obj.color_link_rings.clicked.connect(lambda: pick_color(gui_obj, gui_obj.count_rings, "color_ring_rgba"))
    gui_obj.color_link_weapons.clicked.connect(lambda: pick_color(gui_obj, gui_obj.count_weapons, "color_weapon_rgba"))

    # # link menus
    gui_obj.actionChipy_dev.triggered.connect(lambda: webbrowser.open("www.chipy.dev/me.html"))
    gui_obj.actionGitHub.triggered.connect(lambda: webbrowser.open("https://github.com/iamchipy/chipys-pathofexile-chaos-tool/tree/main/cpct"))
    gui_obj.actionFilterblade_xyz.triggered.connect(lambda: webbrowser.open("https://www.filterblade.xyz/") )
    gui_obj.actionCraftOfExile_com.triggered.connect(lambda: webbrowser.open("https://www.craftofexile.com/en/") )
    gui_obj.actionMap_RegEx.triggered.connect(lambda: webbrowser.open("https://poe.re/#/maps") )
    gui_obj.actionPathOfBuilding_com.triggered.connect(lambda: webbrowser.open("https://pathofbuilding.community/") )
    gui_obj.actionPathOfExile_com.triggered.connect(lambda: webbrowser.open("https://www.pathofexile.com") )
    gui_obj.actionPoE_Lab.triggered.connect(lambda: webbrowser.open("https://www.poelab.com/") )
    gui_obj.actionPoE_Ninja.triggered.connect(lambda: webbrowser.open("https://www.poe.ninja") )
    gui_obj.actionVorici_Calculator.triggered.connect(lambda: webbrowser.open("https://siveran.github.io/calc.html") )
    gui_obj.actionAwakened_PoE_Trade.triggered.connect(lambda: webbrowser.open("https://github.com/SnosMe/awakened-poe-trade") )
    gui_obj.actionPatreon.triggered.connect(lambda: webbrowser.open("https://www.patreon.com/chipysPoEChaosTool") )
    gui_obj.actionInput_ClientSecret.triggered.connect(lambda: request_client_secret() )
    gui_obj.actiondev_button.triggered.connect(lambda: dev_button(gui_obj, parser) )
    
    #ClientSecrect Menu
    # gui_obj.actionInput_ClientSecret.triggered.connect(lambda: receive_client_secret(gui_obj) )

    # # link buttons
    gui_obj.login_link.clicked.connect(lambda: action_login_link(gui_obj, parser))
    gui_obj.refresh_link.clicked.connect(lambda: update_item_filter(gui_obj, parser, True))
    gui_obj.item_filter_browse.clicked.connect(lambda: browser_item_filters(gui_obj))
    gui_obj.client_path_browse.clicked.connect(lambda: browser_client_folder(gui_obj))

    # Link ComboBoxes
    gui_obj.select_league.activated.connect(lambda: action_set_league(gui_obj, parser))
    # gui_obj.select_league.currentIndexChanged.connect(lambda: action_set_league(gui_obj))
    gui_obj.select_tab.activated.connect(lambda: action_set_tab(gui_obj))
    gui_obj.filter_mode.activated.connect(lambda: update_item_filter(gui_obj, parser))
    gui_obj.sets_target.valueChanged.connect(lambda: change_target_count(gui_obj))

    # Link Text
    gui_obj.client_secret_input.textChanged.connect(lambda: receive_client_secret(gui_obj))

@timed_try_wrapper
def action_login_link(gui, parser):
    parser.connect( client_id=user_info.cfg["api"]["CLIENT_ID"],
                    client_secret=user_info.cfg["api"]["CLIENT_SECRET"],
                    scope=user_info.cfg["api"]["SCOPE"],
                    uri=user_info.cfg["api"]["REDIRECT_URI"],
                    manual_token=user_info.cfg["api"]["TOKEN"]
                    )

    # save any token changes
    user_info.set("api","TOKEN", parser.api_handler.token)
    user_info.set("form","username", parser.get_username())
    # gui_main.client_secret_input.isEnabled = False
    gui_main.client_secret_input.setEnabled(False)

    # set login name
    gui.login_link.setText(user_info.get("form","username"))
    gui.login_link.setDisabled(True)
    gui.select_league.setCurrentText( user_info.get("form","league"))
    gui.select_tab.setCurrentText( user_info.get("form","tab"))

    # continue the loading chain
    action_load_leagues(gui)
    
    # report completion
    gui.count_report_string.setText("Successful PathOfExile.com sign-in!")

@timed_try_wrapper
def action_load_leagues(gui):
    global parser
    leagues = parser.get_leagues()

    # clear the box and repop
    gui.select_league.clear()
    gui.select_tab.clear()
    gui.select_league.addItems(leagues)

    # load previous league
    gui.select_league.setCurrentText(user_info.get("form","league"))
    
@timed_try_wrapper
def action_set_league(gui, parser):
    # load current selection for league
    league = gui.select_league.currentText()

    # try pull the league
    action_load_tabs(gui, league, parser)

    # now save changes 
    user_info.set("form", "league",gui.select_league.currentText()) 

@timed_try_wrapper
def action_load_tabs(gui, league, parser):
    tabs = parser.get_tab_names(league).keys()

    # clear the box and repop
    gui.select_tab.clear()
    gui.select_tab.addItems(tabs)

    # select previous tab
    gui.select_tab.setCurrentText(user_info.get("form","tab"))    

@timed_try_wrapper
def action_set_tab(gui, force_recache:bool=False):
    user_info.set("form", "tab", gui.select_tab.currentText())
  
def count_unid_rares(gui, parser, force_recache:bool=False, min_ilvl:int=60)->dict:
    """Function to count unidentified rare items of ilevel

    Args:
        gui (_type_): gui object used for display and update
        force_recache (bool, optional): force a fresh fetch for POE. Defaults to False.

    Returns:
        dict: returns list of count %s (0-100)
    """
    # TODO REMOVE GLOBAL REFERENCE 
    global refresh_off_cooldown, recipe_handler
    league_of_interest = gui.select_league.currentText()

    # put the manual refresh button on cooldown
    refresh_off_cooldown = False
    gui.refresh_link.setEnabled(refresh_off_cooldown)

    try:
        # tab_of_interes
        tab_of_interest = poepy.validate_tab(parser, league_of_interest, gui.select_tab.currentText())
        print("tab_of_interest>",type(tab_of_interest))

        # list of items
        items_of_interest = parser.get_items(tab_of_interest, league_of_interest, force_recache)
        # print("items_of_interest>",type(items_of_interest))

        # filter for unid
        items_unidentified = parser.filter_identified(items_of_interest)
        # print("items_unidentified>",items_unidentified)

        # filter for ilevel
        items_unidentified_ilvl = parser.filter_ilvl(items_unidentified,min_ilvl)
        # print("items_unidentified_ilvl>",items_unidentified_ilvl)

        # filter for rares
        items_unidentified_ilvl_rare = parser.filter_rarity(items_unidentified_ilvl, rarity="rare")
        # print("items_unidentified_ilvl_rare>",items_unidentified_ilvl_rare)
        
        # load recipes
        recipe_handler = poepy.RecipeHandler(items_of_interest)
        #TODO replace slot_counter with RecipeHandler

        # loop and count unids
        # count = poepy.count_slots(parser, items_unidentified_ilvl_rare)
        count = recipe_handler.slot_count

        # Set scales and mutlipliers
        target = gui.sets_target.value()
        multiplier = 100/target

        # convert counts to %
        count["Weapon"] = round(min(100,(count["Weapon"]*multiplier)//2))
        count["Ring"] = round(min(100,(count["Ring"]*multiplier)//2))
        
        count["Helmet"] = round(min(100,count["Helmet"]*multiplier))
        count["Body Armour"] = round(min(100,count["Body Armour"]*multiplier))
        count["Boots"] = round(min(100,count["Boots"]*multiplier))
        count["Gloves"] = round(min(100,count["Gloves"]*multiplier))
        count["Belt"] = round(min(100,count["Belt"]*multiplier))
        count["Amulet"] = round(min(100,count["Amulet"]*multiplier))
        
        # set GUI element values
        gui.count_weapons.setValue(count["Weapon"])
        gui.count_helmets.setValue(count["Helmet"])
        gui.count_bodies.setValue(count["Body Armour"])
        gui.count_boots.setValue(count["Boots"])
        gui.count_gloves.setValue(count["Gloves"])
        gui.count_belts.setValue(count["Belt"])
        gui.count_amulets.setValue(count["Amulet"])
        gui.count_rings.setValue(count["Ring"])
        
        # report
        return count
    except Exception as e:
        print(timestamp(),"count_unid_rares() Error:"+str(e))
        return False

def async_two():
    global refresh_off_cooldown, gui_main, async_time
    elapsed = time.time() - async_time
    # Entry point to secondary exec chain
    log_search()
    # Trigger only every 5 sec
    if elapsed>5 and not refresh_off_cooldown:
        refresh_off_cooldown = True 
        gui_main.refresh_link.setEnabled(refresh_off_cooldown)
    if elapsed > 10:
        async_time = time.time()

@try_wrapper
def log_search():
    """Checks the ClientLog for a maching zone change with timestamp in the current minute
    """
    global modified, previous, gui_main, parser, zone_log, filter_updated
    # 2023/03/30 09:11     
    # 2023/03/30 09:26:41 1117798968 cffb0734 [INFO Client 31504] : You have entered Aspirants' Plaza.     
    snippet = " : You have entered"
    path = user_info.get("form","client_path") + "\logs\Client.txt"
    if not os.path.exists(path):
        return False
    modified = os.path.getmtime(path)
    if modified > previous:
        previous = modified
        # print("Last modified: %s" % time.ctime(modified))
        stamp = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")

        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                if stamp in line and snippet in line and line not in zone_log:
                        print(line)
                        filter_updated = False
                        zone_log.append(line)
                        gui_main.count_report_string.setText(line[78:])
                        update_item_filter(gui_main, parser, force_recache=True)
                        return
        # gui_main.count_report_string.setText("Reading... Done")

@timed_try_wrapper
def browser_item_filters(gui):
    global MainWindow, gui_main
    #C:\Users\chipy\Documents\My Games\Path of Exile\
    file_dialog = QFileDialog(MainWindow)
    file_dialog.setFileMode(QFileDialog.AnyFile)
    file_dialog.setNameFilter("Item Filter (*.filter)")
    file_dialog.setDirectory(user_info.get("form","filter_dir"))
    
    if file_dialog.exec_():
        path = file_dialog.selectedFiles()[0]
        user_info.set("form", "filter_name", path)
        gui.item_filter_browse.setText(os.path.split(path)[1])

@timed_try_wrapper
def browser_client_folder(gui):
    global MainWindow, gui_main
    file_dialog = QFileDialog(MainWindow)
    path = file_dialog.getExistingDirectory(MainWindow, "Select 'Path of Exile' Folder", "C:\Program Files (x86)\Grinding Gear Games")
    user_info.set("form", "client_path", path)
    gui_main.client_path_browse.setText(path[0:22]+"..."+path[-13:])
    
def receive_client_secret(gui):
    global gui_main
    user_info.set("api","client_secret",gui_main.client_secret_input.text())

@timed_try_wrapper
def pick_color(gui, target_object, save_name):
    rgba = user_info.get("form", save_name)
    print(type(rgba),rgba)
    current_color = QtGui.QColor(int(rgba[0]),int(rgba[1]),int(rgba[2]),int(rgba[3]))
    new_color = QColorDialog.getColor(current_color, title=f"Pick a new color for {save_name}")
    if new_color.isValid():
        new_rgba = list(new_color.getRgb())
        user_info.set("form", save_name, str(new_rgba))
        target_object.setStyleSheet(style_sheet_new_color(PROGRESS_BAR_STYLE,new_rgba))
        print(type(new_rgba),new_rgba)

def style_sheet_new_color(base_style:str,new_rgba_color:list) -> str:
    def rgba_t0_hex(rgba:list) -> str:
        r = hex(int(rgba[0]))[2:] 
        g = hex(int(rgba[1]))[2:]
        b = hex(int(rgba[2]))[2:]
        return f"#{r.zfill(2)}{g.zfill(2)}{b.zfill(2)}"
    return_string = ""
    new_hex_color = rgba_t0_hex(new_rgba_color)
    i = base_style.find("background-color: ")
    current_color = base_style[i+18:i+25]
    return_string = base_style.replace(current_color, new_hex_color) 
    return return_string

@timed_try_wrapper
def update_item_filter(gui, parser, force_recache:bool=False, always_show_rings:bool=True, always_show_amulets:bool=True):
    global gui_main, filter_updated, slot_count
    header = poepy.ITEM_FILTER_TITLE_START
    footer = poepy.ITEM_FILTER_TITLE_END
    path = user_info.cfg.get("form","filter_name")
    mode = gui_main.filter_mode.currentText()
    target = 100  # 100% of the goal
    slot_count_percent = count_unid_rares(gui, parser, force_recache)

    if mode == "Disabled":
        return

    # assert isinstance(slot_count_percent, dict)  # If this isn't a dict something didn't pull right from tabs
    if not isinstance(slot_count_percent, dict):
        return False

    # check if filter needs changing
    for key, value in slot_count_percent.items():
        # skip totals
        if key == "Total":
            continue
        if value > 99 and isinstance(slot_count,dict) and slot_count[key] < 100:
            filter_updated = True
            break
    slot_count = slot_count_percent

    # exit case if we don't have a parser object yet
    if not parser or not isinstance(parser, poepy.DataParser):
        return False

    # exit case for when counts could not be found
    if not slot_count_percent:
        print(f"Failed to recieve item counts [slot_count = {slot_count_percent}]")
        return False

    # read data without mod section
    current_filter = ""
    is_section_to_replace=False
    with open(path, "r") as f:
        for line in f:
            if header in line:
                is_section_to_replace = True
            elif footer in line:
                is_section_to_replace = False
            if not is_section_to_replace and footer not in line:
                current_filter += line

    # rebuild filter text adding back in slots as needed   
    prefix = header
    if "Disabled" not in mode:
        print(slot_count_percent)
        if slot_count_percent["Weapon"] < target:
            prefix += poepy.ItemFilterEntry("Weapon",user_info.cfg.get("form","color_weapon_rgba"),width="= 1").to_str()
        if slot_count_percent["Helmet"] < target:
            prefix += poepy.ItemFilterEntry("Helmet",user_info.cfg.get("form","color_helmet_rgba")).to_str()
        if slot_count_percent["Body Armour"] < target:
            prefix += poepy.ItemFilterEntry("Body Armour",user_info.cfg.get("form","color_body_armour_rgba")).to_str()   
        if slot_count_percent["Boots"] < target:
            prefix += poepy.ItemFilterEntry("Boots",user_info.cfg.get("form","color_boots_rgba")).to_str()
        if slot_count_percent["Gloves"] < target:
            prefix += poepy.ItemFilterEntry("Gloves",user_info.cfg.get("form","color_gloves_rgba")).to_str()
        if slot_count_percent["Belt"] < target:
            prefix += poepy.ItemFilterEntry("Belt",user_info.cfg.get("form","color_belt_rgba")).to_str()          
        if always_show_amulets or slot_count_percent["Amulet"] < target:
            prefix += poepy.ItemFilterEntry("Amulet",user_info.cfg.get("form","color_amulet_rgba")).to_str()          
        if always_show_rings or slot_count_percent["Ring"] < target:
            prefix += poepy.ItemFilterEntry("Ring",user_info.cfg.get("form","color_ring_rgba")).to_str()
    prefix += footer

    # write
    with open(path, "w") as f:
        f.write(prefix+current_filter)
    
    # announce update
    t = timestamp()
    n =  os.path.split(path)[1]
    txt = f"{t} '{n}' updated!"
    print(txt)
    gui_main.count_report_string.setText(txt)

    if filter_updated:
        filter_name = str(os.path.split(user_info.get("form", "filter_name"))[1]).split(".")[0]
        path = user_info.get("form","client_path")
        poepy.poe_chat(f"/itemfilter {filter_name}", f"{path}\PathOfExile.exe")
            
@timed_try_wrapper
def request_client_secret():
    global gui_main
    promt_obj = QWidget()
    discord_name, ok = QInputDialog.getText(promt_obj, 'Send Discord Request?', 'Please provide the Discord name (including full "name#1234") to send the secret to')
    if ok:
        post = poepy.request_secret(discord_name)
        print(post)
        if "20" in str(post):
            gui_main.count_report_string.setText('Request has been send please look out for a friend request on Discord')
            # QInputDialog.getText(promt_obj, 'Request Sent', 'Request has been send please look out for a friend request on Discord')

@timed_try_wrapper
def change_target_count(gui):
    user_info.set("form","sets_goal", str(gui.sets_target.value()))

def dev_button(gui:qt.main_gui.Ui_MainWindow, parser:poepy.DataParser):
    global recipe_handler
    recipe_handler.click_items_in_stash(sleep_sec=.01)

if __name__ == "__main__":
    # required for Windows to recognize a Python script as it's own applications and thus have a unique Taskbar Icon
    # https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7/1552105#1552105
    myappid = u'chipy.PoE.chaos.tool' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    # load user file
    user_info.load()

    # build the api/parser object
    api = poepy.PoeApiHandler()
    parser = poepy.DataParser(api_handler = api)

    # build main GUI
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    MainWindow = AsyncMainWindow()
    MainWindow.show()
    gui_main = qt.main_gui.Ui_MainWindow()
    gui_main.setupUi(MainWindow)

    # MainWindow.setWindowFlags(MainWindow.windowFlags() | Qt.WindowStaysOnTopHint)
    # MainWindow.setAttribute(Qt.WA_TranslucentBackground)
    # MainWindow.setWindowFlags(Qt.FramelessWindowHint)

    # Modify the gui with connections and links
    apply_ui_connections(gui_main, parser)  # here we modify actions to the GUI
    apply_ui_defaults(gui_main, MainWindow, app)  # set default values for the form when it's made

    # run app as the last thing in the script
    sys.exit(app.exec_())
  