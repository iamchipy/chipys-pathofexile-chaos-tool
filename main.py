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
import json
import lib.poepy
import lib.user_info

# type checking block (AND RUFF INFO)
# https://www.youtube.com/watch?v=bcAqceZkZRQ
if typing.TYPE_CHECKING:
    ...

# set statics
ASYNC_INTERVAL_MS = 2000

api:lib.poepy.PoeApiHandler
parser:lib.poepy.DataParser

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

def apply_ui_defaults():
    global gui_main
    head, filter_name = os.path.split(lib.user_info.cfg["form"]["filter_dir"])
    gui_main.item_filter_browse.setText(filter_name)

def apply_ui_connections():
    """Overlay that connects up the GUI so that we can modularly replace the gui.py from QT5
    Args:
        gui_obj (gui.Ui_MainWindow): Main window GUI object
    """
    global gui_main, MainWindow

    # set window icon
    app.setWindowIcon(QtGui.QIcon('.\img\ChipyLogo.png'))
    MainWindow.setWindowTitle("Chipy's PoE Tools")

    # set login icon (this is to fix the image path issue)
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap("./img/poe.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    gui_main.login_link.setIcon(icon)

    # # link menus
    gui_main.actionChipy_dev.triggered.connect(lambda: trigger_website("chipy"))
    gui_main.actionFilterblade_xyz.triggered.connect(lambda: trigger_website("filterblade"))

    # # link buttons
    gui_main.login_link.clicked.connect(lambda: action_login_link(gui_main))
    gui_main.refresh_link.clicked.connect(lambda: update_unid_counts(gui_main, True))
    gui_main.item_filter_browse.clicked.connect(lambda: open_browser())

    # Link ComboBoxes
    gui_main.select_league.currentIndexChanged.connect(lambda: action_set_league(gui_main))
    gui_main.select_tab.currentIndexChanged.connect(lambda: action_set_tab(gui_main))

def trigger_website(short_name:str):
    if short_name == "chipy":
        webbrowser.open("www.chipy.dev/me.html")
    if short_name == "filterblade":
        webbrowser.open("https://www.filterblade.xyz/")        

def action_login_link(gui):
    global api, parser, gui_main
    api = lib.poepy.PoeApiHandler(client_id=lib.user_info.cfg["api"]["CLIENT_ID"],
                                    client_secret=lib.user_info.cfg["api"]["CLIENT_SECRET"],
                                    scope=lib.user_info.cfg["api"]["SCOPE"],
                                    uri=lib.user_info.cfg["api"]["REDIRECT_URI"],
                                    manual_token=lib.user_info.cfg["api"]["TOKEN"]
                                    )
    parser = lib.poepy.DataParser(api_handler = api)

    # save any token changes
    lib.user_info.cfg["api"]["TOKEN"] = api.token
    lib.user_info.cfg["form"]["username"] = json.loads(api.get_profile().content)["name"]
    lib.user_info.save()

    # set login name
    gui.login_link.setText(lib.user_info.cfg["form"]["username"])
    gui.login_link.setDisabled(True)
    gui.select_league.setCurrentText( lib.user_info.cfg["form"]["league"])
    gui.select_tab.setCurrentText( lib.user_info.cfg["form"]["tab"])

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
    # gui_main.select_league.setCurrentText( lib.user_info.cfg["form"]["league"])
    
def action_set_league(gui):
    league = gui.select_league.currentText()
    lib.user_info.cfg["form"]["league"] = gui.select_league.currentText()
    lib.user_info.save()    
    action_load_tabs(gui, league)

def action_load_tabs(gui, league):
    global parser, gui_main
    tabs = parser.get_tab_names(league).keys()
    # clear the box and repop
    gui.select_tab.clear()
    gui.select_tab.addItems(tabs)
    
def action_set_tab(gui, force_recache:bool=False):
    global parser, gui_main
    lib.user_info.cfg["form"]["tab"] = gui.select_tab.currentText()
    lib.user_info.save()
  
def update_unid_counts(gui, force_recache:bool=False):
    global parser, gui_main
    league_of_interest = gui.select_league.currentText()
    try:
        # tab_of_interes
        tabs_of_interest = lib.poepy.validate_tab(parser, league_of_interest, gui.select_tab.currentText())

        # filter for unid
        list_of_items_unidentified = parser.filter_identified(parser.get_items(tabs_of_interest, league_of_interest, force_recache))
        
        # loop and count unids
        count = lib.poepy.count_slots(parser, list_of_items_unidentified)
        target = gui.sets_target.value()
        # str_count = str(count.items())
        # gui.count_report_string.setText(str_count)
        multiplier = 100//target
        
        # set GUI element values
        gui_main.count_weapons.setValue(count["Weapon"]*multiplier)
        gui_main.count_helms.setValue(count["Helmet"]*multiplier)
        gui_main.count_bodies.setValue(count["Body"]*multiplier)
        gui_main.count_boots.setValue(count["Boots"]*multiplier)
        gui_main.count_gloves.setValue(count["Gloves"]*multiplier)
        gui_main.count_belts.setValue(count["Belt"]*multiplier)
        gui_main.count_amulets.setValue(count["Amulet"]*multiplier)
        gui_main.count_rings.setValue((count["Ring"]*multiplier)/2)
    except Exception as e:
        gui.count_report_string.setText(str(e))

def async_two():
    # Entry point to secondary exec chain
    log_search()

def log_search():
    global modified, previous, gui_main
    # 2023/03/30 09:11     
    # 2023/03/30 09:26:41 1117798968 cffb0734 [INFO Client 31504] : You have entered Aspirants' Plaza.     
    snippet = " : You have entered"
    path = "C:\Program Files (x86)\Grinding Gear Games\Path of Exile\logs\Client.txt"
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

def open_browser():
    global MainWindow
    #C:\Users\chipy\Documents\My Games\Path of Exile\
    file_dialog = QFileDialog(MainWindow)
    file_dialog.setFileMode(QFileDialog.AnyFile)
    file_dialog.setNameFilter("Item Filter (*.filter)")
    file_dialog.setDirectory(lib.user_info.cfg["form"]["filter_dir"])
    
    if file_dialog.exec_():
        lib.user_info.cfg["form"]["filter_dir"] = file_dialog.selectedFiles()[0]
        lib.user_info.save()

if __name__ == "__main__":
    # required for Windows to recognize a Python script as it's own applications and thus have a unique Taskbar Icon
    # https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7/1552105#1552105
    myappid = u'chipy.tools.PoE' # arbitrary string
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
  