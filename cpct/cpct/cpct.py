import typing
import datetime
import os
import sys
import time
import webbrowser
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QApplication, QColorDialog, QInputDialog, QWidget
from PyQt5 import QtGui
from PyQt5.QtCore import QTimer
import qt.main_gui
import ctypes
import poepy
import user_info
from __about__ import __version__

# PoE dev Docs for ref
# https://www.pathofexile.com/developer/docs
# TYPE/Structures
# https://www.pathofexile.com/developer/docs/reference#type-Item

# type checking block (AND RUFF INFO)
# https://www.youtube.com/watch?v=bcAqceZkZRQ
if typing.TYPE_CHECKING:
    ...

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

api:poepy.PoeApiHandler
parser:poepy.DataParser

# variables for searching log files to detect new zone
modified = 0
async_time = time.time()
previous = 0
refresh_off_cooldown = True

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

def try_wrapper(function):
    """Simple wrapper that includes a TRY loop
    Args:
        function (Func): Returns the provided function wrapped Try
    """
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as e:
            print(function.__name__, "=> FAILED:", e)
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
            print(function.__name__, "=> FAILED:",end-start, e)
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
    gui_obj.count_amulets.setStyleSheet(style_sheet_new_color(PROGRESS_BAR_STYLE, user_info.get("form", "color_amulets")))
    gui_obj.count_belts.setStyleSheet(style_sheet_new_color(PROGRESS_BAR_STYLE, user_info.get("form", "color_amulets")))
    gui_obj.count_bodies.setStyleSheet(style_sheet_new_color(PROGRESS_BAR_STYLE, user_info.get("form", "color_bodies")))
    gui_obj.count_boots.setStyleSheet(style_sheet_new_color(PROGRESS_BAR_STYLE, user_info.get("form", "color_boots")))
    gui_obj.count_gloves.setStyleSheet(style_sheet_new_color(PROGRESS_BAR_STYLE, user_info.get("form", "color_gloves")))
    gui_obj.count_helmets.setStyleSheet(style_sheet_new_color(PROGRESS_BAR_STYLE, user_info.get("form", "color_helmets")))
    gui_obj.count_rings.setStyleSheet(style_sheet_new_color(PROGRESS_BAR_STYLE, user_info.get("form", "color_rings")))
    gui_obj.count_weapons.setStyleSheet(style_sheet_new_color(PROGRESS_BAR_STYLE, user_info.get("form", "color_weapons")))

    # defaults for item_filter modes
    gui_obj.filter_mode.addItems(["Default","FilterBlade","Custom","Disabled"])
    
def apply_ui_connections(gui_obj):
    """Overlay that connects up the GUI so that we can modularly replace the gui.py from QT5
    https://www.geeksforgeeks.org/function-wrappers-in-python/
    Args:
        gui_obj (gui.Ui_MainWindow): Main window GUI object
    """


    # Link ColorPickers
    gui_obj.color_link_amulets.clicked.connect(lambda: pick_color(gui_obj, gui_obj.count_amulets, "color_amulets"))
    gui_obj.color_link_belts.clicked.connect(lambda: pick_color(gui_obj, gui_obj.count_belts, "color_belts"))
    gui_obj.color_link_bodies.clicked.connect(lambda: pick_color(gui_obj, gui_obj.count_bodies, "color_bodies"))
    gui_obj.color_link_boots.clicked.connect(lambda: pick_color(gui_obj, gui_obj.count_boots, "color_boots"))
    gui_obj.color_link_gloves.clicked.connect(lambda: pick_color(gui_obj, gui_obj.count_gloves, "color_gloves"))
    gui_obj.color_link_helmets.clicked.connect(lambda: pick_color(gui_obj, gui_obj.count_helmets, "color_helmets"))
    gui_obj.color_link_rings.clicked.connect(lambda: pick_color(gui_obj, gui_obj.count_rings, "color_rings"))
    gui_obj.color_link_weapons.clicked.connect(lambda: pick_color(gui_obj, gui_obj.count_weapons, "color_weapons"))

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
    
    #ClientSecrect Menu
    # gui_obj.actionInput_ClientSecret.triggered.connect(lambda: receive_client_secret(gui_obj) )

    # # link buttons
    gui_obj.login_link.clicked.connect(lambda: action_login_link(gui_obj))
    gui_obj.refresh_link.clicked.connect(lambda: count_unid_rares(gui_obj, True))
    gui_obj.item_filter_browse.clicked.connect(lambda: browser_item_filters(gui_obj))
    gui_obj.client_path_browse.clicked.connect(lambda: browser_client_folder(gui_obj))

    # Link ComboBoxes
    gui_obj.select_league.currentIndexChanged.connect(lambda: action_set_league(gui_obj))
    gui_obj.select_tab.currentIndexChanged.connect(lambda: action_set_tab(gui_obj))
    gui_obj.filter_mode.currentIndexChanged.connect(lambda: update_item_filter(gui_obj))
    gui_obj.sets_target.valueChanged.connect(lambda: change_target_count(gui_obj))

    # Link Text
    gui_obj.client_secret_input.textChanged.connect(lambda: receive_client_secret(gui_obj))

@timed_try_wrapper
def action_login_link(gui):
    global api, parser, gui_main
    api = poepy.PoeApiHandler(client_id=user_info.cfg["api"]["CLIENT_ID"],
                                    client_secret=user_info.cfg["api"]["CLIENT_SECRET"],
                                    scope=user_info.cfg["api"]["SCOPE"],
                                    uri=user_info.cfg["api"]["REDIRECT_URI"],
                                    manual_token=user_info.cfg["api"]["TOKEN"]
                                    )
    parser = poepy.DataParser(api_handler = api)

    # save any token changes
    user_info.set("api","TOKEN", api.token)
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

    # set previous league
    gui_main.select_league.setCurrentText(user_info.get("form","league"))
    
@timed_try_wrapper
def action_set_league(gui):
    # load current selection for league
    league = gui.select_league.currentText()
    # print("League:",league)
    if league != "":
        try:
            previous = user_info.get("form", "league")
            # print("previous:",previous)
            action_load_tabs(gui, previous)
        except Exception as e:
            print("action_set_league::>",e)
            user_info.set("form", "league",gui.select_league.currentText()) 
            action_load_tabs(gui, league)

@timed_try_wrapper
def action_load_tabs(gui, league):
    global parser, gui_main
    tabs = parser.get_tab_names(league).keys()
    # clear the box and repop
    gui.select_tab.clear()
    gui.select_tab.addItems(tabs)
    
@timed_try_wrapper
def action_set_tab(gui, force_recache:bool=False):
    global parser, gui_main
    user_info.set("form", "tab", gui.select_tab.currentText())
  
@timed_try_wrapper
def count_unid_rares(gui, force_recache:bool=False)->list[list, int]:
    global refresh_off_cooldown, parser
    league_of_interest = gui.select_league.currentText()

    # put the manual refresh button on cooldown
    refresh_off_cooldown = False
    gui_main.refresh_link.setEnabled(refresh_off_cooldown)

    # TODO Auto filter reload "/itemfilter 0PKKgH0"

    try:
        # tab_of_interes
        tabs_of_interest = poepy.validate_tab(parser, league_of_interest, gui.select_tab.currentText())
        print("tabs_of_interest>",type(tabs_of_interest))

        # list of items
        items_of_interest = parser.get_items(tabs_of_interest, league_of_interest, force_recache)
        print("items_of_interest>",type(items_of_interest))

        # filter for unid
        items_unidentified = parser.filter_identified(items_of_interest)
        print("items_unidentified>",items_unidentified)

        # filter for ilevel
        items_unidentified_ilvl = parser.filter_ilvl(items_unidentified)
        print("items_unidentified_ilvl>",items_unidentified_ilvl)

        # filter for rares
        items_unidentified_ilvl_rare = parser.filter_rarity(items_unidentified_ilvl, rarity="rare")
        print("items_unidentified_ilvl_rare>",items_unidentified_ilvl_rare)
        
        # loop and count unids
        count = poepy.count_slots(parser, items_unidentified_ilvl_rare)
        # gui_main.count_report_string.setText(f"Count Total: {count['Total']}")

        # Set scales and mutlipliers
        target = gui.sets_target.value()
        multiplier = 100//target

        # set GUI element values
        gui_main.count_weapons.setValue(count["Weapon"]*multiplier)
        gui_main.count_helmets.setValue(count["Helmet"]*multiplier)
        gui_main.count_bodies.setValue(count["Body Armor"]*multiplier)
        gui_main.count_boots.setValue(count["Boot"]*multiplier)
        gui_main.count_gloves.setValue(count["Glove"]*multiplier)
        gui_main.count_belts.setValue(count["Belt"]*multiplier)
        gui_main.count_amulets.setValue(count["Amulet"]*multiplier)
        gui_main.count_rings.setValue((count["Ring"]*multiplier)//2)
        
        # report
        return [count, target]
    except Exception as e:
        t = str(time.time())[-1:]
        gui.count_report_string.setText("ERR:"+str(e)+f"[{t}]")
        return [False, False]

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
    global modified, previous, gui_main, parser
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
        # gui_main.count_report_string.setText("Reading...")
        stamp = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                if stamp in line and snippet in line:
                        print(line)
                        gui_main.count_report_string.setText(line[78:])
                        count_unid_rares(gui_main)
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
    current_color = QtGui.QColor(user_info.get("form", save_name))
    new_color = QColorDialog.getColor(current_color, title=f"Pick a new color for {save_name}")
    if new_color.isValid():
        user_info.set("form", save_name, new_color.name())
        user_info.set("form", save_name+"_rgb", str(list(new_color.getRgb())))
        target_object.setStyleSheet(style_sheet_new_color(PROGRESS_BAR_STYLE,new_color.name()))
        update_item_filter(gui)

def style_sheet_new_color(base_style:str,new_color:str) -> str:
    return_string = ""
    i = base_style.find("background-color: ")
    current_color = base_style[i+18:i+25]
    return_string = base_style.replace(current_color, new_color) 
    return return_string

@timed_try_wrapper
def update_item_filter(gui):
    global gui_main
    header = poepy.ITEM_FILTER_TITLE_START
    footer = poepy.ITEM_FILTER_TITLE_END
    path = user_info.cfg.get("form","filter_name")
    mode = gui_main.filter_mode.currentText()
    slot_count, target = count_unid_rares(gui)

    # exit case for when counts could not be found
    if not slot_count:
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
        print(slot_count)
        if slot_count["Weapon"] >= target:
            prefix += poepy.ItemFilterEntry("Weapon",user_info.cfg.get("form","color_weapons_rgb"),width="= 1").to_str()
        if slot_count["Helmet"] >= target:
            prefix += poepy.ItemFilterEntry("Helmet",user_info.cfg.get("form","color_helmets_rgb")).to_str()
        if slot_count["Body Armor"] >= target:
            prefix += poepy.ItemFilterEntry("Body Armour",user_info.cfg.get("form","color_bodies_rgb")).to_str()   
        if slot_count["Boot"] >= target:
            prefix += poepy.ItemFilterEntry("Boot",user_info.cfg.get("form","color_boots_rgb")).to_str()
        if slot_count["Glove"] >= target:
            prefix += poepy.ItemFilterEntry("Glove",user_info.cfg.get("form","color_gloves_rgb")).to_str()
        if slot_count["Amulet"] >= target:
            prefix += poepy.ItemFilterEntry("Amulet",user_info.cfg.get("form","color_amulets_rgb")).to_str()
        if slot_count["Ring"] >= target:
            prefix += poepy.ItemFilterEntry("Ring",user_info.cfg.get("form","color_rings_rgb")).to_str()
    prefix += footer

    # write
    with open(path, "w") as f:
        f.write(prefix+current_filter)
    
    # announce update
    gui_main.count_report_string.setText("Filter updated . . .")
            
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

if __name__ == "__main__":
    # load user file
    user_info.load()

    # required for Windows to recognize a Python script as it's own applications and thus have a unique Taskbar Icon
    # https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7/1552105#1552105
    myappid = u'chipy.PoE.chaos.tool' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    # build main GUI
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    MainWindow = AsyncMainWindow()
    MainWindow.show()
    gui_main = qt.main_gui.Ui_MainWindow()
    gui_main.setupUi(MainWindow)

    # Modify the gui with connections and links
    apply_ui_connections(gui_main)  # here we modify actions to the GUI
    apply_ui_defaults(gui_main, MainWindow, app)  # set default values for the form when it's made

    # run app as the last thing in the script
    sys.exit(app.exec_())
  