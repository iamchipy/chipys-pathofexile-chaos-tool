
import json
from poe_oauth import PoeApiHandler
from base_types import BASE_TYPES
import user_info



class DataParser():
    def __init__(self, api_handler:PoeApiHandler=None, league="standard") -> None:
        if not api_handler:
            print("API object missing. MAKE sure to use '.new_api_handler(api_handler)'")
        self.api_handler = api_handler

        self.league = league
        self.cached = {"DEFAULT_VALUE":0}

    def _cache_stash(self, league:str):
        self.cached[league+"_stash_response"] = self.api_handler.get_stash(league)
        # print(type(self.cached[league+"_stash_response"]))
        self.cached[league+"_stash"] = json.loads(self.cached[league+"_stash_response"].content)["stashes"]
        # print(self.cached[league+"_stash"])
    
    def _parse_tab_names(self, stash:dict, filter_remove_only=True) -> dict:
        result = [[i["name"],i["id"]] for i in stash]
        
        if filter_remove_only:
            result = [i for i in result if "Remove-only" not in i[0]]

        return dict(result)
    
    def get_tab_names(self, league="standard") -> dict:
        if league+"_stash" not in self.cached:
            self._cache_stash(league)
        self.cached[league+"_tab_names"] = self._parse_tab_names(stash=self.cached[league+"_stash"])
        return self.cached[league+"_tab_names"]
        
    def _cache_tab(self, league:str, stash_id:str):
        self.cached[league+"_"+stash_id+"_response"] = self.api_handler.get_tab(league, stash_id)
        raw=json.loads(self.cached[league+"_"+stash_id+"_response"].content)
        # print(raw)
        # assert "children" not in raw["stash"]  # assert not a parent/nested tab
        self.cached[league+"_"+stash_id] = raw["stash"]["items"]

    def _parse_item_names(self, tab:dict) -> list:
        result = [[i["name"],i["id"]] for i in tab]
        return result      

    def get_item_names(self,  stash_id:str="52dc1b3814", league="hardcore") -> dict:
        if league+"_"+stash_id not in self.cached:
            self._cache_tab(league,stash_id)
        self.cached[league+"_"+stash_id+"_items"] = self._parse_item_names(self.cached[league+"_"+stash_id])
        return self.cached[league+"_"+stash_id+"_items"] 
    
    def get_items(self,  stash_id:str="52dc1b3814", league="hardcore") -> dict:
        if league+"_"+stash_id not in self.cached:
            self._cache_tab(league,stash_id)
        self.cached[league+"_"+stash_id+"_items"] = self._parse_item_names(self.cached[league+"_"+stash_id])
        return self.cached[league+"_"+stash_id] 
    
    def get_items_filtered(self,  haystack:list) -> list:
        return [i for i in haystack if i["identified"] is False]

    def _cache_characters(self):
        self.cached["characters_response"] = self.api_handler.get_characters()
        self.cached["characters"] = json.loads(self.cached["characters_response"].content)["characters"]

    def _parse_character_names(self, characters):
        result = [[i["name"],i["league"]] for i in characters]
        return result      
    
    def get_characters(self) -> list:
        if "characters" not in self.cached:
            self._cache_characters()
        return self._parse_character_names(self.cached["characters"])   

    def _cache_leagues(self):
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
        if "leagues" not in self.cached:
            self._cache_leagues()
        return self._parse_league_names(self.cached["leagues"] )

def set_league(parser:DataParser, user_input:str=None):
    active_leagues = parser.get_leagues()
    if not user_input:
        user_input = input("Select League: ").lower()
    for league in active_leagues:
        if user_input in str(league).lower():
            print("League auto-corrected to:",league)
            return league
    return False

def set_tab(parser:DataParser, user_input:str=None):
    tab_names = parser.get_tab_names(league_of_interest)
    if not user_input:
        user_input = input("Select tab: ").lower()
    for tab in tab_names.items():
        if user_input in str(tab).lower():
            print("League auto-corrected to:",tab)
            return tab
    return False

def index_unid(parser:DataParser, list_of_items:list):
    counts={"a":1}
    for item in list_of_items:
        slot = BASE_TYPES[item["baseType"]]
        if slot in counts:
            counts[slot] +=1
        else:
            counts[slot] = 1
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
    league_of_interest = set_league(parser, "stand")

    # tab_of_interes
    tab_of_interest = set_tab(parser, "dt")

    # filter for unid
    list_of_items_unidentified = parser.get_items_filtered(parser.get_items(tab_of_interest[1],league_of_interest))
    
    # loop and count unids
    print(index_unid(parser, list_of_items_unidentified))
 

