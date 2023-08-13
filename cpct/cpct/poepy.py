import asyncio
import hashlib
import json
import random
import time
import webbrowser
from urllib.parse import parse_qs, urlparse
import psutil
import pywinauto
import pyautogui

from discord import TOKEN_STATIC
from base64 import urlsafe_b64decode
from __about__ import __version__

import requests
import websockets

from base_types import SLOT_LOOKUP, WEAPON_LIST, SLOT_LIST

HEADER_USER_AGENT ={"User-Agent": "OAuth chipytools/0.0.1 (Contact: contact@chipy.dev)"}
HEADER_TYPE = {"Content-Type": "application/x-www-form-urlencoded"}
URL_AUTH = r"https://www.pathofexile.com/oauth/authorize"
URL_TOKEN = r"https://www.pathofexile.com/oauth/token"
API_ENDPOINT = r"https://api.pathofexile.com/"
API_PROFILE = API_ENDPOINT+"profile"
API_CHARACTER = API_ENDPOINT+"character"
API_LEAGUE = API_ENDPOINT+"league"
API_STASH = API_ENDPOINT+"stash/"

DEPTH_ITEMS = 2
DEPTH_STASH_NAMES = 1

ITEM_FILTER_TITLE_START = "# START -- Chipy's PoE Chaos Tool\n"
ITEM_FILTER_TITLE_END = "# END -- Chipy's PoE Chaos Tool\n"

FRAMETYPE_NORMAL = 0
FRAMETYPE_MAGIC = 1
FRAMETYPE_RARE = 2
FRAMETYPE_UNIQUE = 3
FRAMETYPE_GEM = 4
FRAMETYPE_CURRENCY = 5
FRAMETYPE_DIVINATIONCARD = 6
FRAMETYPE_QUEST = 7
FRAMETYPE_PROPHECY = 8
FRAMETYPE_FOIL = 9
FRAMETYPE_SUPPORTERFOIL = 10

RECIPE_CHAOS = 60
RECIPE_REGAL = 75 

"""
PROCESS
- Connection handler
- - Calls
- - - Output data
- Data handler
- - processer
- - 
"""

class PoeApiHandler():
    def __init__(self) -> None:
        self.connected = False

    def connect(self, 
                 client_id, 
                 client_secret, 
                 uri, 
                 scope="account:profile", 
                 force_re_auth:bool=False, 
                 manual_token:str=None):
        print("Building variables . . . ",end=" ")
        self.id = client_id
        self.secret = client_secret
        self.uri = uri
        self.state = hashlib.sha256(str(random.randint(2341,8599)).encode()).hexdigest()
        self.scope = scope
        self.code = ""
        self.token = ""
        self.headers = {**HEADER_TYPE,**HEADER_USER_AGENT}  
        print("done")

        if manual_token:
            self._update_header_token(manual_token)
        self._authenticate(force_re_auth)
        self.connect = True
        print( "done")
        

    async def parse(self, url):
        
        print("Parsing . . . ", end="")
        self.url_dict = urlparse(url)
        queries = parse_qs(self.url_dict[4])  
        if "error" in queries:
            print("PROBLEM WITH OAUTH REPLY:")        
            print(queries)
            exit()
        self.state=queries["state"][0]
        self.code=queries["code"][0]

    async def echo(self, websocket, path):
        async for message in websocket:
            await websocket.send(message)
            print("done")
            self.msg = message
            await self.parse(self.msg)
            self._exit.set_result(None)
            print("done")
                
    async def echo_server(self):
        async with websockets.serve(self.echo, '127.0.0.1', 32111):
            await self._exit       

    def _update_header_token(self,token_to_update_with=False):
        if token_to_update_with:
            self.token = token_to_update_with
        self.headers = {"Authorization": "Bearer "+self.token, 
                        **HEADER_USER_AGENT}
        print("LOADING TOKEN:",self.token)
        
    def is_request_successful(self, request_code:str):
        if "200" in str(request_code):
            return 1
        if "400" in str(request_code):
            print("Bad Request: Please check user config for ClientSecret")
        return False
        
    def _still_authenticated(self):
        if self.is_request_successful(self.get_stash("standard")):
            return True
        print("FAILED with cached token")
        return False
            
    def _authenticate(self, force_re_auth=False):
        print("Authenticating . . . ",end="")
        # test status
        if self._still_authenticated() and not force_re_auth:
            return
        
        try:
            if self.renew_auth_token():
                return
        except Exception as e:
            print("AuthRenewError:",e)
            pass 
        # Building URL for permission request
        # print("Building request ...")
        client_str = '?client_id='+self.id
        response_type = '&response_type=code'
        scope_str = '&scope='+self.scope
        state_str = '&state='+self.state
        redir = '&redirect_uri='+self.uri

        # print("Initializing OAuth2 ...")
        webbrowser.open(URL_AUTH+client_str+response_type+scope_str+state_str+redir)
        # print(URL_AUTH+client_str+response_type+scope_str+state_str+redir)

        # Start the async loop
        print("Waiting for approval . . . ",end="")
        self.loop = asyncio.get_event_loop()
        self._exit = asyncio.Future() 
        self.loop.run_until_complete(self.echo_server())

        # build variables for the exchange
        self.token_data = { "client_id":self.id,
                            "client_secret": self.secret,
                            "grant_type":"authorization_code",
                            "code":self.code,
                            "redirect_uri":self.uri,
                            "scope":self.scope}
        
        self.headers = {**HEADER_TYPE,**HEADER_USER_AGENT}       
         
        # Make the code -> token exchange
        request = requests.post(URL_TOKEN, data=self.token_data, headers=self.headers)
        # request.raise_for_status()

        # check for issues:
        if self.is_request_successful(request):
            self.auth_reply_raw = json.loads(request.content)
            self._update_header_token(self.auth_reply_raw["access_token"])
        
    def renew_auth_token(self):
        self.body_refresh = {"client_secret":self.secret,
                             "grant_type":"refresh_token",
                             "refresh_token":self.auth_reply_raw["refresh_token"]}
        request = requests.post(URL_TOKEN, data=self.token_data, headers=self.headers)
        request.raise_for_status()

        self.auth_reply_raw = json.loads(request.content)
        self._update_header_token(self.auth_reply_raw["access_token"])
        return self._still_authenticated()

    def get_stash(self, league) -> requests.Response:
        r = requests.get(API_STASH+league, headers=self.headers)
        if self.is_request_successful(r):
            return r
        return False    
    
    def get_profile(self) -> requests.Response:
        r = requests.get(API_PROFILE, headers=self.headers)
        if self.is_request_successful(r):
            return r
        return False
    
    def get_tab(self, league:str, stash_id:str) -> requests.Response:
        r = requests.get(API_STASH+league+"/"+stash_id, headers=self.headers)
        if self.is_request_successful(r):
            return r
        return False    
    
    def get_leagues(self) -> requests.Response:
        # this is a service scope request so it's a bit different
        # (not private so no auth needed)
        #https://www.pathofexile.com/developer/docs/authorization#client_credentials
        # first get a token
        data = {"client_id":self.id,
                "client_secret": self.secret,
                "grant_type":"client_credentials",
                "scope":"service:leagues"}
        r = requests.post(URL_TOKEN, data=data, headers={**HEADER_TYPE,
                                                         **HEADER_USER_AGENT} )
        # adjust a temp header
        temp_header = {**HEADER_TYPE,
                       **HEADER_USER_AGENT,
                       "Authorization":"Bearer "+json.loads(r.content)["access_token"]}
        r = requests.get(API_LEAGUE, headers=temp_header)  
        if self.is_request_successful(r):
            return r
        return False  
    
    def get_characters(self) -> requests.Response:
        r = requests.get(API_CHARACTER, headers=self.headers) 
        if self.is_request_successful(r):
            return r
        return False       

class DataParser():
    def __init__(self, api_handler:PoeApiHandler=None, league="standard") -> None:
        if not api_handler:
            print("API object missing. MAKE sure to use '.new_api_handler(api_handler)'")  
        self.api_handler = api_handler

        self.league = league
        self.cached = {"DEFAULT_VALUE":0}

    def connect(self,
                client_id, 
                client_secret, 
                uri, 
                scope="account:profile", 
                force_re_auth:bool=False, 
                manual_token:str=None):
        self.api_handler.connect(client_id=client_id, 
                                 client_secret=client_secret, 
                                 uri=uri, 
                                 scope=scope, 
                                 force_re_auth=force_re_auth, 
                                 manual_token=manual_token)
    
    def connection_precheck(self):
        return self.api_handler.connected

    def _cache_stash(self, league:str,force_recache:bool=False):
        """Caches the list of tabs in a league's stash |get_leagues(self) -> list:|
            {'id': 'fae1b5d2ef', 
            'name': 'Heist (Remove-only)', 
            'type': 'NormalStash', 
            'index': 0, 
            'metadata': {'colour': '7c5436'}}

        Args:
            league (str): league name as 
        """


        if league+"_stash_response" not in self.cached or force_recache:
            print("Caching "+league+"_stash")
            self.cached[league+"_stash_response"] = self.api_handler.get_stash(league)
            self.cached[league+"_stash"] = json.loads(self.cached[league+"_stash_response"].content)["stashes"]
    
    def _parse_tab_names(self, stash:dict, filter_remove_only=True) -> dict:
        result = [[i["name"],i["id"]] for i in stash]
        if filter_remove_only:
            result = [i for i in result if "Remove-only" not in i[0]]
        return dict(result)
    
    def find_tab(self, 
                 search_str:str, 
                 league:str="standard", 
                 all_matches:bool=False) -> tuple:
        """Searches for the provided str in both tab names and IDs

        Args:
            search_str (str): Partial or complete case sensitive string to find
            league (str, optional): League Name string. Defaults to "standard".

        Returns:
            tuple: tab's (name, ID) pair
        """
        # first cache the data we need use
        self._cache_stash(league)

        # set some helper to assist with matching
        last_match = None
        name_match = []
        prioritize_name = len(search_str) != 10

        # handle when search is a tuple from Find_STash()
        if isinstance(search_str, tuple):
            search_str = search_str[1]

        # search stashes for a match
        for tab in self.cached[league+"_stash"]:
            # check for any partial match
            if search_str in tab["name"] or search_str in tab["id"]:
                # load into variable 
                last_match = (tab["name"],tab["id"],tab["type"])
                # print("something:", last_match)
                # full match return right away
                if search_str == tab["name"] or search_str == tab["id"]:
                    # print("FULLMATCH------------------")
                    return last_match          
                # store name match for priority      
                if prioritize_name and search_str in tab["name"]:
                    # if all_matches:
                    #     name_match.append((tab["name"], tab["id"]))
                    # else:
                    name_match = (tab["name"], tab["id"])
                    # print("nameMatch", name_match)
        if prioritize_name:
            return name_match
        return last_match
       
    def get_tab_names(self, league="standard") -> dict:
        self._cache_stash(league)
        self.cached[league+"_tab_names"] = self._parse_tab_names(stash=self.cached[league+"_stash"])
        return self.cached[league+"_tab_names"]
        
    def _cache_tab(self, league:str, stash_id:str, force_recache:bool=False) -> dict:
        if league+"_"+stash_id not in self.cached or force_recache:
            print("Caching "+league+"_"+stash_id)
            self.cached[league+"_"+stash_id+"_response"] = self.api_handler.get_tab(league, stash_id)
            raw=json.loads(self.cached[league+"_"+stash_id+"_response"].content)
            # print(type(raw))
            # print(type(raw["stash"]))
            # print(type(raw["stash"]["items"]))
            assert "children" not in raw["stash"]  # assert not a parent/nested tab
            self.cached[league+"_"+stash_id] = raw
        return self.cached[league+"_"+stash_id]

    def get_tab_type(self,tab_of_interest, league_of_interest, force_recache:bool=False):

        tab_info = self.find_tab(tab_of_interest, league_of_interest)
        # tab = self.cached[f"{league_of_interest}_{tab_id}"]
        print(tab_info)
        return tab_info[2]

    def _parse_item_names(self, tab:dict) -> list:
        # print(tab)
        # print(type(tab))
        result = [i["name"] for i in tab["stash"]["items"]]
        return result      

    def get_item_names(self,  stash_id:str="52dc1b3814", league="hardcore") -> dict:
        self._cache_tab(league,stash_id)
        self.cached[league+"_"+stash_id+"_item_names"] = self._parse_item_names(self.cached[league+"_"+stash_id])
        return self.cached[league+"_"+stash_id+"_item_names"] 
    
    def get_items(self, 
                  stash_id:str="52dc1b3814", 
                  league="hardcore", 
                  force_recache:bool=False) -> dict:
        # handle when Stash_ID is False
        if isinstance(stash_id, bool):
            return False
        # handle when Stash_ID is the name/ID tuple
        if isinstance(stash_id,tuple) and len(stash_id)==3:
            stash_id=stash_id[1]
        # Handle when you are given a list of StashID
        if isinstance(stash_id,list):
            result_list = []
            for stash in stash_id:
                fetch = self.get_items(stash, league)
                if fetch:
                    result_list+=fetch
            # print(result_list)
            return result_list            

        assert isinstance(stash_id,str) and len(stash_id)==10  # Assert valid stashID 
        self._cache_tab(league,stash_id, force_recache)
        # return self.cached[league+"_"+stash_id]["stash"]["items"]
        try:
            return self.cached[league+"_"+stash_id]["stash"]["items"]
        except KeyError as e:
            print(f"Failed to get stash: {stash_id} [no key 'items' in object] {e}")
            return False
    
    def filter_identified(self, list_of_items:list) -> list:
        return [i for i in list_of_items if i["identified"] is False]
    
    def filter_ilvl(self, list_of_items:list, ilvl:int=60) -> list:
        return [i for i in list_of_items if i["ilvl"] >= 60]
    
    def filter_rarity(self, list_of_items:list, rarity:str="rare") -> list:
        # TODO-LOW build the rest of the frametypes
        # print([i["frameType"] for i in list_of_items ])
        if rarity == "rare":
            return [i for i in list_of_items if i["frameType"] == FRAMETYPE_RARE]
        print("Filtering for rarity '{rarity}' isn't supported yet")
        return [i for i in list_of_items if i["frameType"] == FRAMETYPE_MAGIC]        

    def _cache_profile(self):
        if "profile" not in self.cached:
            print("Caching Profile")
            self.cached["profile_response"] = self.api_handler.get_profile()
            self.cached["profile_name"] = json.loads(self.cached["profile_response"].content)["name"]
    
    def get_username(self) -> str:
        self._cache_profile()
        return self.cached["profile_name"]

    def _cache_characters(self):
        if "characters" not in self.cached:
            print("Caching Characters")
            self.cached["characters_response"] = self.api_handler.get_characters()
            self.cached["characters"] = json.loads(self.cached["characters_response"].content)["characters"]

    def _parse_character_names(self, characters):
        result = [[i["name"],i["league"]] for i in characters]
        return result      
    
    def get_characters(self) -> list:
        self._cache_characters()
        return self._parse_character_names(self.cached["characters"])   

    def _cache_leagues(self):
        if "leagues" not in self.cached:
            print("Caching Leagues")
            self.cached["leagues_response"] = self.api_handler.get_leagues()
            self.cached["leagues"] = json.loads(self.cached["leagues_response"].content)["leagues"]

    def _parse_league_names(self, characters):
        result = [i["id"] for i in characters if i["realm"] == "pc"]
        return result  

    def get_leagues(self) -> list:
        """Base leagues:
            - 'Standard'
            - 'Hardcore'
            - 'SSF Standard'
            - 'SSF Hardcore'
        Returns:
            list: List of active leagues
        """
        self._cache_leagues()
        return self._parse_league_names(self.cached["leagues"])

class ItemFilterEntry():
    def __init__(self, 
                 _class:str,
                 bg_color:list,
                 ilvl:str=">= 60",
                 width:str="<= 2",
                 height:str="<= 3" ,
                 mirror_mode:bool=None) -> None:
        self.show = True
        self.HasInfluence = mirror_mode
        self.Rarity = "Rare"
        self.Identified = False
        self.ItemLevel = ilvl  # ">= 60"
        self.Class = _class  # "Amulets"
        self.Sockets = "< 6"
        self.LinkedSockets = "< 5"
        self.Width = width
        self.Height = height     
        self.SetFontSize = 40
        # self.SetTextColor = [255, 255, 255, 255]
        # self.SetBorderColor = [0, 0, 0]
        self.SetBackgroundColor = bg_color
        # self.MinimapIcon = "2 White Star"
        # self.CustomAlertSound = '"1maybevaluable.mp3" 300'
        # self.PlayEffect = "Red"

        if isinstance(bg_color,list):
            self.SetBackgroundColor = f"{bg_color[0]} {bg_color[1]} {bg_color[2]} {bg_color[3]}"

    def _class_list_to_string(self, incoming_list:list):
        result = ""
        for item in incoming_list:
            result += "\""+item+"\" "
        return result

    def to_str(self):
        out_str = ""
        for key, value in self.__dict__.items():
            # Case key = show/hide
            if "show" in key:
                out_line = "Show\n" if value else "Hide\n"
            else:
                # more fancy checking of assignment op
                if isinstance(value,str):
                    if any(op in value for op in ["<",">","="]):
                        out_line = "\t%s %s\n" % (key, value)
                    elif any(t in key for t in ["Class"]):
                        if value == "Weapon":
                            out_line = '\t%s %s\n' % (key, self._class_list_to_string(WEAPON_LIST))
                        else:
                            out_line = '\t%s "%s"\n' % (key, value)
                    else:
                        out_line = '\t%s %s\n' % (key, value)                      
                else:
                    out_line = "\t%s %s\n" % (key, value)
                # remove list walls
                out_line = out_line.replace("[","")
                out_line = out_line.replace(",","")
                out_line = out_line.replace("]","")                    
            out_str += out_line
        return out_str

class PoEItemWrapper():
    def __init__(self, poe_item) -> None:

        # save raw data
        self.raw = poe_item
        if isinstance(poe_item, str):
            self.raw = json.loads(poe_item)
        
        # print(self.raw)
        """{'verified': False, 'w': 2, 'h': 2, 'icon': 'https://web.poecdn.com/gen/image/WzI1LDE0LHsiZiI6IjJESXRlbXMvQXJtb3Vycy9Cb290cy9Cb290c1N0ckRleDMiLCJ3IjoyLCJoIjoyLCJzY2FsZSI6MX1d/3418ad050e/BootsStrDex3.png', 'league': 'Crucible', 'id': '0cd21f0cab26e2c7f2e8f6291cb289af14c8d2ae6ccfaf2f5b22dcfac3766c97', 'sockets': [{'group': 0, 'attr': 'D', 'sColour': 'G'}, {'group': 1, 'attr': 'S', 'sColour': 'R'}], 'name': '', 'typeLine': 'Wyrmscale Boots', 'baseType': 'Wyrmscale Boots', 'identified': False, 'ilvl': 85, 'properties': [{'name': 'Armour', 'values': [['98', 0]], 'displayMode': 0, 'type': 16}, {'name': 'Evasion Rating', 'values': [['98', 0]], 'displayMode': 0, 'type': 17}], 'requirements': [{'name': 'Str', 'values': [['48', 0]], 'displayMode': 1, 'type': 63}, {'name': 'Dex', 'values': [['48', 0]], 'displayMode': 1, 'type': 64}], 'frameType': 2, 'x': 16, 'y': 12, 'inventoryId': 'Stash1', 'socketedItems': []}"""
        
        # extract info we care about
        self.hash = self.raw["id"]
        self.x = self.raw["x"]
        self.y = self.raw["y"]
        self.w = self.raw["w"]
        self.h = self.raw["h"]
        self.rarity = self.raw["frameType"]
        self.identified = self.raw["identified"]
        self.ilvl = self.raw["ilvl"]
        # print("IN>",self.raw["baseType"])
        self.slot = SLOT_LOOKUP.get(self.raw["baseType"], "Unknown")
        # print("OUT>",self.slot)

    def coords(self):
        return "xy top left coords in grid"

    def size(self):
        return "dimentions"
    
    def __repr__(self) -> str:
        simplified_info = self.__dict__
        del simplified_info["raw"]
        # del simplified_info["hash"]
        return str(simplified_info)
    
    # def __iter__(self):
    #     for attribute in dir(self):
    #         print(attribute)
    #         if not attribute.startswith("___"):
    #             yield attribute

    
class RecipeHandler():
    RECIPE = {"Weapon":4,
              "Helmet":2,
              "Body Armour":2,
              "Boots":2,
              "Gloves":2,
              "Belt":2,
              "Amulet":2,
              "Ring":4}    
    def __init__(self, list_of_items:list) -> None:
        print("Init RecipeHandler > ", end="")
        self.assigned_hashes = []
        self.ready_recipes = []
        self.slot_count= {"Weapon":0,
                          "Helmet":0,
                          "Body Armour":0,
                          "Boots":0,
                          "Gloves":0,
                          "Belt":0,
                          "Amulet":0,
                          "Ring":0,
                          "Unknown":0}  
        self.quad_1440 = StashGrid([18,175,866,1023])  
        #TODO-HIGH build ui input option for screen size
        #TODO-LOW build auto-dection options

        print("parsing > ", end="")
        self.list_of_items = [item for item in self.simplify_items(list_of_items) if item.rarity==2]
        #TODO-HIGH this needs to be replaced with self._fetch_item()

        print("tallying items > ", end="")
        self._tally_slots()

        print("Count:",self.slot_count," DONE")
        # self.display_stash_locations()

    def _tally_slots(self):
        for item in self.list_of_items:
            if item.slot in self.slot_count:    
                self.slot_count[item.slot] +=1
                # print("Found a", item.slot, ">>",self.slot_count[item.slot])

    def _fetch_item(self, 
                    slot:str, 
                    ilvl_range:list[int,int]=[60,99], 
                    identified:bool=False, 
                    frame_type:int=FRAMETYPE_RARE) -> PoEItemWrapper:
        assert isinstance(ilvl_range, list)

        for item in self.list_of_items:
            # check if hash has been assigned
            if item.hash in self.assigned_hashes:
                continue

            # check if item matches desired details
            # if item.slot == slot and ilvl_range[0]<= item.ilvl <= ilvl_range[1] and item.identified == identified and item.rarity == frame_type:
            #     self.assigned_hashes.append(item.hash)
            #     return item

            if item.slot != slot:
                # print(f"{slot} not satisfied by {item}") 
                continue
            
            # if 60 - 74 =>     60 > 84 > 74
            if ilvl_range[0] > item.ilvl or item.ilvl > ilvl_range[1]:
                # print(f"{ilvl_range} failed iLvl -> in {item}") 
                continue                
                
            if item.identified != identified:
                # print(f"{identified} isn't unid -> in {item}") 
                continue  

            if item.rarity != frame_type:
                # print(f"{frame_type} wrong frame -> in {item}") 
                continue      

            # if we made it this far we know it's a good fit           
            self.assigned_hashes.append(item.hash)
            return item
        return None

    def _collect_ingredients(self, recipe_mode:int=RECIPE_CHAOS, identified:bool=False, frame_type:int=FRAMETYPE_RARE) -> list[PoEItemWrapper]:
        
        # Set iLvl requirements (assuming the case to be Chaos we only check for regal)
        requires_one_below_75 = True
        if recipe_mode > 74:
            requires_one_below_75 = False

        ingredients = {}
        for ingredient, quantity in self.RECIPE.items():
            for index in range(quantity):
                # ask for ingredient below 75 if need, until met
                if requires_one_below_75:
                    item = self._fetch_item(ingredient, [60,74], identified, frame_type)
                    if item:
                        requires_one_below_75 = False
                        print("SELECTED FOR FORCE iLEVEL:",item)
                    else:
                        item = self._fetch_item(ingredient, [60,100], identified, frame_type)
                else:
                    item = self._fetch_item(ingredient, [60,100], identified, frame_type)
                ingredients[ingredient+"_"+str(index)] = item
        return ingredients          

    def display_stash_locations(self, count:int=2):
        ingredients = self._collect_ingredients()
        assert isinstance(ingredients, dict)  # just to make sure we got the right things

        if not self.is_recipe_complete(ingredients):
            print("Recipe missing ingredient!")
            return False
    
        for ingredient, item in ingredients.items():
            print(ingredient,item.x,item.y,type(item))

    def is_recipe_complete(self, recipe_set:dict) -> bool:
        if None in recipe_set.values():
            print("Set containing 'none':", [slot for slot, item in recipe_set.items() if item is None])
            return False
        return True

    def simplify_items(self,raw_item_list_json:list)->list[PoEItemWrapper]:
        processed_list = []
        for item in raw_item_list_json:
            processed_list.append(PoEItemWrapper(item))
        return processed_list
    
    def _click_inv_grid(self,grid_coords:list[int,int], sleep_sec):
        coords = self.quad_1440.center_in_tile(self.quad_1440.grid2pixel_coords(grid_coords))
        print("moving:",grid_coords,coords)
        pyautogui.moveTo(coords[0], coords[1])
        time.sleep(sleep_sec/2)
        pyautogui.click()
        time.sleep(sleep_sec)

    def click_items_in_stash(self, sleep_sec:float=0.2):

        ingredients = self._collect_ingredients()
        if not self.is_recipe_complete(ingredients):
            print("Recipe missing ingredient")
            return False
        
        # start sequence
        pyautogui.keyDown('ctrl')  
        time.sleep(sleep_sec)    
        for ingredient, item in ingredients.items():
            print(ingredient)
            self._click_inv_grid([item.x,item.y],sleep_sec)
  
        pyautogui.keyUp('ctrl')        
    
class StashGrid():
    quad_grid = [[[r+1,c+1] for r in range(24)] for c in range(24)]

    def __init__(self,pixel_coords:list[int,int,int,int], grid_type:int=2) -> None:
        if grid_type == 2:
            self.grid_size = len(self.quad_grid[0])
            # print(self.grid_size)
        self.pixel_coords = pixel_coords
        self.left_trim_pixel = pixel_coords[0]
        self.top_trim_pixel = pixel_coords[1]
        self.tile_size = (pixel_coords[2] - pixel_coords[0])/self.grid_size
        # print(self.quad_grid)
    
    def grid2pixel_coords(self,grid_coords:list)-> list[int,int]:
        x_margin = self.left_trim_pixel
        x_distance = (grid_coords[0])*self.tile_size
        x = x_margin+x_distance
        y_margin = self.top_trim_pixel
        y_distance = (grid_coords[1])*self.tile_size
        y = y_margin+y_distance      
        return [x,y]
    
    def center_in_tile(self,pixel_coords:list)-> list[int,int]:
        x = pixel_coords[0]+self.tile_size/2
        y = pixel_coords[1]+self.tile_size/2
        return [x,y]
    
def validate_league(parser:DataParser, user_input:str=None):
    active_leagues = parser.get_leagues()
    if not user_input:
        print(active_leagues)
        user_input = input("Select League: ").lower()
    for league in active_leagues:
        if user_input in str(league).lower():
            print("League auto-corrected to:",league)
            return league
    return False

def validate_tab(parser:DataParser,
                 league_of_interest:str=None, 
                 user_input:str=None) -> tuple:
    if not user_input:
        print(parser.get_tab_names(league_of_interest))
        user_input = input("Select tab: ")
    if not league_of_interest:
        league_of_interest =validate_league(parser)

    tab = parser.find_tab(user_input, league_of_interest)

    if tab:
        print("League auto-corrected to:",tab)
        return tab
    return False

def count_slots(parser:DataParser, list_of_items:list, include_all_unid:bool=False):
    counts={"Total":0,
            "Weapon":0,
            "Helmet":0,
            "Body Armour":0,
            "Boots":0,
            "Gloves":0,
            "Belt":0,
            "Amulet":0,
            "Ring":0}
    for item in list_of_items:
        slot = SLOT_LOOKUP.get(item["baseType"], "Unknown")
        if slot in counts or include_all_unid:
            counts[slot] +=1
            counts["Total"] += 1      
    return counts

def request_secret(user_name:str="Demo"):
    try:
        ip = requests.get("https://api.ipify.org", timeout=1).content
        data = {"content":f"New request for ClientSecret from '**{user_name}**'@{ip}v{__version__}"}
    except Exception as e:    # noqa: F841
        # print(e)
        data = {"content":f"New request for ClientSecret from '**{user_name}**'v{__version__}"}

    r = requests.post(urlsafe_b64decode(TOKEN_STATIC),data=data, timeout=5)
    return r

def _list_pywinauto_window_text(filter:str=""):
    import pywinauto
    import win32gui
    windows = pywinauto.findwindows.find_windows()
    for handle in windows:
        title = win32gui.GetWindowText(handle)
        if filter in title:
            print(title)    


def poe_chat(msg:str,poe_exe_path:str, auto_send:bool=True):    
    def _get_pid_of_exe_path(exe_path:str):
        """Get the executable path of the process associated with the given window handle."""
        for process in psutil.process_iter(['pid', 'exe']):
            if process.info['exe'] == exe_path:
                # print(process.info['pid'])
                return process.info['pid']

    pid = _get_pid_of_exe_path(poe_exe_path)
    # check for "PathOfExile.exe"
    poe = pywinauto.Application().connect(process=pid)
    # print(poe)
    poe.PathOfExile.type_keys("{ENTER}"+msg+"{ENTER}", with_spaces=True, pause=0.00)


if __name__ == "__main__":
    pass
    # pid = _get_pid_of_exe_path(r"C:\Program Files (x86)\Grinding Gear Games\Path of Exile\PathOfExile.exe")
    # poe_chat("/itemfilter dl",pid)
