import asyncio
import hashlib
import json
import random
import requests
import websockets
import webbrowser
from urllib.parse import urlparse, parse_qs

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
    def __init__(self, client_id, client_secret, uri, scope="account:profile", force_re_auth:bool=False, manual_token:str=None):
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
        print( "done")
        

    async def parse(self, url):
        
        print("Parsing . . . ", end="")
        self.url_dict = urlparse(url)
        queries = parse_qs(self.url_dict[4])  #{'code': ['28bf9a843e5626d47a125ad384fe53f6e998335f'], 'state': ['fa6437e646eabcd1a575a81a06c94a1f74abc68d16bac2414d004241233c8b76']}
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
        
    def _success_code_200(self, request_test):
        if "200" in str(request_test):
            return True
        return False

    def _still_authenticated(self):
        if self._success_code_200(self.get_stash("standard")):
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
            #LOGGING
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
        request.raise_for_status()

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
        # return json.loads(requests.get(API_STASH+league, headers=self.headers).content)
        return requests.get(API_STASH+league, headers=self.headers)
    
    def get_profile(self) -> requests.Response:
        # return json.loads(requests.get(API_PROFILE, headers=self.headers).content)
        return requests.get(API_PROFILE, headers=self.headers)
    
    def get_tab(self, league:str, stash_id:str) -> requests.Response:
        return requests.get(API_STASH+league+"/"+stash_id, headers=self.headers)
    
    def get_leagues(self) -> requests.Response:
        # this is a service scope request so it's a bit different (not private so no auth needed)
        #https://www.pathofexile.com/developer/docs/authorization#client_credentials
        # first get a token
        data = {"client_id":self.id,
                "client_secret": self.secret,
                "grant_type":"client_credentials",
                "scope":"service:leagues"}
        r = requests.post(URL_TOKEN, data=data, headers={**HEADER_TYPE,**HEADER_USER_AGENT} )
        # adjust a temp header
        temp_header = {**HEADER_TYPE,
                       **HEADER_USER_AGENT,
                       "Authorization":"Bearer "+json.loads(r.content)["access_token"]}
        return requests.get(API_LEAGUE, headers=temp_header)    
    
    def get_characters(self) -> requests.Response:
        return requests.get(API_CHARACTER, headers=self.headers)    

# {'verified': False, 
#  'w': 1, 
#  'h': 1, 
#  'icon': 'https://web.poecdn.com/gen/image/WzI1LDE0LHsiZiI6IjJESXRlbXMvR2Vtcy9TdXBwb3J0L0luY3JlYXNlZFF1YW50aXR5IiwidyI6MSwiaCI6MSwic2NhbGUiOjF9XQ/306f059231/IncreasedQuantity.png', 
#  'support': True, 
#  'league': 'Standard', 
#  'id': '03fbe5019da2870ebab84aaeb7c8c2e6402b36a7547432164204be756832612d', 
#  'name': '', 
#  'typeLine': 'Item Quantity Support', 
#  'baseType': 'Item Quantity Support', 
#  'identified': True, 
#  'ilvl': 0, 
#  'properties': [{'name': 'Support', 
#                  'values': [], 
#                  'displayMode': 0}, 
#                     {'name': 'Level', 
#                     'values': [['17', 0]], 
#                     'displayMode': 0, 
#                     'type': 5}], 
#                  'requirements': [{'name': 'Level', 
#                                    'values': [['64', 0]], 
#                                    'displayMode': 0, 
#                                    'type': 62}, 
#                  {'name': 'Str', 
#                   'values': [['102', 0]], 
#                   'displayMode': 1, 
#                   'type': 63}], 
#                 'additionalProperties': [{'name': 'Experience', 
#                                           'values': [['3719002/26185582', 0]], 
#                                           'displayMode': 2, 
#                                           'progress': 0.14, 
#                                           'type': 20}], 
#                 'secDescrText': 'Supports any skill that can kill enemies.', 
#                 'explicitMods': ['33% increased Quantity of Items Dropped by Enemies Slain from Supported Skills'], 
#                 'descrText': 'This is a Support Gem. It does not grant a bonus to your character, but to skills in sockets connected to it. Place into an item socket connected to a socket containing the Active Skill Gem you wish to augment. Right click to remove from a socket.',
#                 'frameType': 4, 
#                 'x': 28, 
#                 'y': 0, 
#                 'inventoryId': 'Stash1'},

