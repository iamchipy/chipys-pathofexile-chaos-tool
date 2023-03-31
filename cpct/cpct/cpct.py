import typing
import datetime
import os
import sys
import time
import webbrowser
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QApplication
from PyQt5 import QtGui
from PyQt5.QtCore import QTimer
import qt.main_gui
import ctypes
import poepy
import user_info

# type checking block (AND RUFF INFO)
# https://www.youtube.com/watch?v=bcAqceZkZRQ
if typing.TYPE_CHECKING:
    ...

# set statics
ASYNC_INTERVAL_MS = 2000

api:poepy.PoeApiHandler
parser:poepy.DataParser

# variables for searching log files to detect new zone
modified = 0
previous = 0

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

def apply_ui_defaults():
    global gui_main
    gui_main.item_filter_browse.setText(os.path.split(user_info.get("form", "filter_name"))[1])
    gui_main.client_secret_input.setText(user_info.get("api","client_secret"))
    gui_main.client_path_browse.setText(user_info.get("form", "client_path")[0:22]+"..."+user_info.get("form", "client_path")[-13:])

def apply_ui_connections():
    """Overlay that connects up the GUI so that we can modularly replace the gui.py from QT5
    https://www.geeksforgeeks.org/function-wrappers-in-python/
    Args:
        gui_obj (gui.Ui_MainWindow): Main window GUI object
    """
    global gui_main, MainWindow

    # set window Icons
    app.setWindowIcon(QtGui.QIcon('./cpct/cpct/img/ChipyLogo.png'))
    MainWindow.setWindowTitle("Chipy's PoE Chaos Tool")
    
    # set login icon (this is to fix the image path issue)
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap("./cpct/cpct/img/poe.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    gui_main.login_link.setIcon(icon)

    # # link menus
    gui_main.actionChipy_dev.triggered.connect(lambda: webbrowser.open("www.chipy.dev/me.html"))
    gui_main.actionGitHub.triggered.connect(lambda: webbrowser.open("https://github.com/iamchipy/chipys-pathofexile-chaos-tool/tree/main/cpct"))
    gui_main.actionFilterblade_xyz.triggered.connect(lambda: webbrowser.open("https://www.filterblade.xyz/") )
    gui_main.actionCraftOfExile_com.triggered.connect(lambda: webbrowser.open("https://www.craftofexile.com/en/") )
    gui_main.actionMap_RegEx.triggered.connect(lambda: webbrowser.open("https://poe.re/#/maps") )
    gui_main.actionPathOfBuilding_com.triggered.connect(lambda: webbrowser.open("https://pathofbuilding.community/") )
    gui_main.actionPathOfExile_com.triggered.connect(lambda: webbrowser.open("https://www.pathofexile.com") )
    gui_main.actionPoE_Lab.triggered.connect(lambda: webbrowser.open("https://www.poelab.com/") )
    gui_main.actionPoE_Ninja.triggered.connect(lambda: webbrowser.open("https://www.poe.ninja") )
    gui_main.actionVorici_Calculator.triggered.connect(lambda: webbrowser.open("https://siveran.github.io/calc.html") )
    gui_main.actionAwakened_PoE_Trade.triggered.connect(lambda: webbrowser.open("https://github.com/SnosMe/awakened-poe-trade") )
    
    #ClientSecrect Menu
    # gui_main.actionInput_ClientSecret.triggered.connect(lambda: receive_client_secret(gui_main) )

    # # link buttons
    gui_main.login_link.clicked.connect(lambda: action_login_link(gui_main))
    gui_main.refresh_link.clicked.connect(lambda: update_unid_counts(gui_main, True))
    gui_main.item_filter_browse.clicked.connect(lambda: browser_item_filters(gui_main))
    gui_main.client_path_browse.clicked.connect(lambda: browser_client_folder(gui_main))

    # Link ComboBoxes
    gui_main.select_league.currentIndexChanged.connect(lambda: action_set_league(gui_main))
    gui_main.select_tab.currentIndexChanged.connect(lambda: action_set_tab(gui_main))

    # Link Text
    gui_main.client_secret_input.textChanged.connect(lambda: receive_client_secret(gui_main))

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

def action_load_leagues(gui):
    global parser
    leagues = parser.get_leagues()
    # clear the box and repop
    gui.select_league.clear()
    gui.select_tab.clear()
    gui.select_league.addItems(leagues)
    # # set previous league
    # gui_main.select_league.setCurrentText( user_info.cfg["form"]["league"])
    
def action_set_league(gui):
    league = gui.select_league.currentText()
    user_info.cfg["form"]["league"] = gui.select_league.currentText()
    user_info.save()    
    action_load_tabs(gui, league)

def action_load_tabs(gui, league):
    global parser, gui_main
    tabs = parser.get_tab_names(league).keys()
    # clear the box and repop
    gui.select_tab.clear()
    gui.select_tab.addItems(tabs)
    
def action_set_tab(gui, force_recache:bool=False):
    global parser, gui_main
    user_info.cfg["form"]["tab"] = gui.select_tab.currentText()
    user_info.save()
  
def update_unid_counts(gui, force_recache:bool=False):
    global parser, gui_main
    league_of_interest = gui.select_league.currentText()
    try:
        # tab_of_interes
        tabs_of_interest = poepy.validate_tab(parser, league_of_interest, gui.select_tab.currentText())

        # filter for unid
        list_of_items_unidentified = parser.filter_identified(parser.get_items(tabs_of_interest, league_of_interest, force_recache))
        
        # loop and count unids
        count = poepy.count_slots(parser, list_of_items_unidentified)
        gui_main.count_report_string.setText(f"Count Total: {count['Total']}")

        # Set scales and mutlipliers
        target = gui.sets_target.value()
        multiplier = 100//target

        # set GUI element values
        gui_main.count_weapons.setValue(count["Weapon"]*multiplier)
        gui_main.count_helms.setValue(count["Helmet"]*multiplier)
        gui_main.count_bodies.setValue(count["Body"]*multiplier)
        gui_main.count_boots.setValue(count["Boots"]*multiplier)
        gui_main.count_gloves.setValue(count["Gloves"]*multiplier)
        gui_main.count_belts.setValue(count["Belt"]*multiplier)
        gui_main.count_amulets.setValue(count["Amulet"]*multiplier)
        gui_main.count_rings.setValue((count["Ring"]*multiplier)//2)
    except Exception as e:
        gui.count_report_string.setText("ERR:"+str(e))

def async_two():
    # Entry point to secondary exec chain
    log_search()

@try_wrapper
def log_search():
    global modified, previous, gui_main
    # 2023/03/30 09:11     
    # 2023/03/30 09:26:41 1117798968 cffb0734 [INFO Client 31504] : You have entered Aspirants' Plaza.     
    snippet = " : You have entered"
    path = user_info.get("form","client_path") + "\logs\Client.txt"
    modified = os.path.getmtime(path)
    if modified > previous:
        previous = modified
        print("Last modified: %s" % time.ctime(modified))
        gui_main.count_report_string.setText("Reading...")
        stamp = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                if stamp in line and snippet in line:
                        print(line)
                        gui_main.count_report_string.setText(line[78:])
                        update_unid_counts(gui_main)
                        return
        gui_main.count_report_string.setText("Reading... Done")

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

if __name__ == "__main__":
    # load user file
    user_info.load()

    # required for Windows to recognize a Python script as it's own applications and thus have a unique Taskbar Icon
    # https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7/1552105#1552105
    myappid = u'chipy.PoE.chaos.tool' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    # build main GUI
    app = QApplication(sys.argv)
    MainWindow = AsyncMainWindow()
    MainWindow.show()
    gui_main = qt.main_gui.Ui_MainWindow()
    gui_main.setupUi(MainWindow)

    # Modify the gui with connections and links
    apply_ui_connections()  # here we modify actions to the GUI
    apply_ui_defaults()  # set default values for the form when it's made

    # run app as the last thing in the script
    sys.exit(app.exec_())
  