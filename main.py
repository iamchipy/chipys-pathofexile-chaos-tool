
import json
from poe_oauth import PoeApiHandler
from base_types import SLOT_LOOKUP
import user_info



class DataParser():
    def __init__(self, api_handler:PoeApiHandler=None, league="standard") -> None:
        if not api_handler:
            print("API object missing. MAKE sure to use '.new_api_handler(api_handler)'")
        self.api_handler = api_handler

        self.league = league
        self.cached = {"DEFAULT_VALUE":0}

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
            self.cached[league+"_stash_response"] = self.api_handler.get_stash(league)
            self.cached[league+"_stash"] = json.loads(self.cached[league+"_stash_response"].content)["stashes"]
    
    def _parse_tab_names(self, stash:dict, filter_remove_only=True) -> dict:
        result = [[i["name"],i["id"]] for i in stash]
        if filter_remove_only:
            result = [i for i in result if "Remove-only" not in i[0]]
        return dict(result)
    
    def find_tab(self, search_str:str, league:str="standard", all_matches:bool=False) -> tuple:
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

        # search stashes for a match
        for tab in self.cached[league+"_stash"]:
            # check for any partial match
            if search_str in tab["name"] or search_str in tab["id"]:
                # load into variable 
                last_match = (tab["name"],tab["id"])
                # print("something:", last_match)
                # full match return right away
                if search_str == tab["name"] or search_str == tab["id"]:
                    return last_match          
                # store name match for priority      
                if prioritize_name and search_str in tab["name"]:
                    if all_matches:
                        name_match.append((tab["name"], tab["id"]))
                    else:
                        name_match = (tab["name"], tab["id"])
                    # print("nameMatch", name_match)
        if prioritize_name:
            # if all_matches:
            #     return name_match
            return name_match
        return last_match
       
    def get_tab_names(self, league="standard") -> dict:
        self._cache_stash(league)
        self.cached[league+"_tab_names"] = self._parse_tab_names(stash=self.cached[league+"_stash"])
        return self.cached[league+"_tab_names"]
        
    def _cache_tab(self, league:str, stash_id:str, force_recache:bool=False) -> dict:
        if league+"_"+stash_id not in self.cached or force_recache:
            self.cached[league+"_"+stash_id+"_response"] = self.api_handler.get_tab(league, stash_id)
            raw=json.loads(self.cached[league+"_"+stash_id+"_response"].content)
            # print(type(raw))
            # print(type(raw["stash"]))
            # print(type(raw["stash"]["items"]))
            assert "children" not in raw["stash"]  # assert not a parent/nested tab
            self.cached[league+"_"+stash_id] = raw
        return self.cached[league+"_"+stash_id]

    def _parse_item_names(self, tab:dict) -> list:
        # print(tab)
        # print(type(tab))
        result = [i["name"] for i in tab["stash"]["items"]]
        return result      

    def get_item_names(self,  stash_id:str="52dc1b3814", league="hardcore") -> dict:
        self._cache_tab(league,stash_id)
        self.cached[league+"_"+stash_id+"_item_names"] = self._parse_item_names(self.cached[league+"_"+stash_id])
        return self.cached[league+"_"+stash_id+"_item_names"] 
    
    def get_items(self, stash_id:str="52dc1b3814", league="hardcore") -> dict:
        # handle when Stash_ID is False
        if isinstance(stash_id, bool):
            return False
        # handle when Stash_ID is the name/ID tuple
        if isinstance(stash_id,tuple) and len(stash_id)==2:
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
        self._cache_tab(league,stash_id)
        # return self.cached[league+"_"+stash_id]["stash"]["items"]
        try:
            return self.cached[league+"_"+stash_id]["stash"]["items"]
        except KeyError as e:
            print(f"Failed to get stash: {stash_id} [no key 'items' in object]")
            return False
    
    def filter_identified(self, list_of_items:list) -> list:
        return [i for i in list_of_items if i["identified"] is False]

    def _cache_characters(self):
        if "characters" not in self.cached:
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

def validate_tab(parser:DataParser,league_of_interest:str=None, user_input:str=None) -> tuple:
    if not user_input:
        print(parser.get_tab_names(league_of_interest))
        user_input = input("Select tab: ")
    if not league_of_interest:
        league_of_interest =validate_league(parser)

    tab = parser.find_tab(user_input, league_of_interest)

    if tab:
        print("League auto-corrected to: ",tab)
        return tab
    return False

def count_slots(parser:DataParser, list_of_items:list):
    counts={"Total":0}
    for item in list_of_items:
        if item["baseType"] not in SLOT_LOOKUP:
            slot = "Unknown"
        else:
            slot = SLOT_LOOKUP[item["baseType"]]
        if slot in counts:
            counts[slot] +=1
        else:
            counts[slot] = 1
        counts["Total"] += 1
    
    return counts

if __name__ == "__main__":
    authentication = PoeApiHandler(client_id=user_info.cfg["api"]["CLIENT_ID"],
                                   client_secret=user_info.cfg["api"]["CLIENT_SECRET"],
                                   scope=user_info.cfg["api"]["SCOPE"],
                                   uri=user_info.cfg["api"]["REDIRECT_URI"],
                                   manual_token=user_info.cfg["api"]["TOKEN"]
                                   )
    parser = DataParser(api_handler = authentication)

    # save any token changes
    user_info.cfg["api"]["TOKEN"] = authentication.token
    user_info.save()

    # set league
    league_of_interest = validate_league(parser, "st")

    # tab_of_interes
    tabs_of_interest = [validate_tab(parser, league_of_interest, "DT"),
                        validate_tab(parser, league_of_interest, "S Cluster"),
                        validate_tab(parser, league_of_interest, "g")]


    # filter for unid
    list_of_items_unidentified = parser.filter_identified(parser.get_items(tabs_of_interest, league_of_interest))
    
    # loop and count unids
    print(count_slots(parser, list_of_items_unidentified))
    # print(parser.get_item_names(tab_of_interest[1],league_of_interest))
 

