import asyncio
import hashlib
import json
import random
import requests
import websockets
import webbrowser
from urllib.parse import urlparse, parse_qs

HEADER_USER_AGENT = {"User-Agent": "OAuth chipytools/0.0.1 (Contact: contact@chipy.dev)"}
HEADER_TYPE = {"Content-Type": "application/x-www-form-urlencoded"}
URL_AUTH = r"https://www.pathofexile.com/oauth/authorize"
URL_TOKEN = r"https://www.pathofexile.com/oauth/token"
API_ENDPOINT = r"https://api.pathofexile.com/"
API_PROFILE = API_ENDPOINT+"profile"
API_CHARACTER = API_ENDPOINT+"character"
API_LEAGUE = API_ENDPOINT+"league"
API_STASH = API_ENDPOINT+"stash/"

DEPTH_ITEMS = 2

class PoeApiHandler():
    def __init__(self, client_id, client_secret, uri, scope="account:stashes", force_re_auth:bool=False, manual_token:str=None):
        print("Building variables ...")
        self.id = client_id
        self.secret = client_secret
        self.uri = uri
        self.state = hashlib.sha256(str(random.randint(2341,8599)).encode()).hexdigest()
        self.scope = scope
        self.code = ""
        self.token = ""

        self.headers = {**HEADER_TYPE,**HEADER_USER_AGENT}  
        if manual_token:
            self._update_header_token(manual_token)
   
        self._authenticate(force_re_auth)

    async def parse(self, url):
        print("Parsing...")
        self.url_dict = urlparse(url)
        queries = parse_qs(self.url_dict[4])  #{'code': ['28bf9a843e5626d47a125ad384fe53f6e998335f'], 'state': ['fa6437e646eabcd1a575a81a06c94a1f74abc68d16bac2414d004241233c8b76']}
        self.state=queries["state"][0]
        self.code=queries["code"][0]

    async def echo(self, websocket, path):
        async for message in websocket:
            await websocket.send(message)
            print("Received data:", message)
            self.msg = message
            await self.parse(self.msg)
            self._exit.set_result(None)
                
    async def echo_server(self):
        async with websockets.serve(self.echo, '127.0.0.1', 32111):
            print('Awaiting authentication...')
            await self._exit
        print('Done')        

    def _update_header_token(self,token_to_update_with=False):
        if token_to_update_with:
            self.token = token_to_update_with
        self.headers = {"Authorization": "Bearer "+self.token,
                        **HEADER_USER_AGENT}
        print("NEW TOKEN:",self.token)
        
    def _success_code_200(self, request_test):
        if "200" in str(request_test):
            return True
        return False

    def _still_authenticated(self):
        if self._success_code_200(self._get_stash_raw("standard")):
            return True
        print("FAILED INIT AUTH")
        return False
            
    def _authenticate(self, force_re_auth=False):
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
        print("Building request ...")
        client_str = '?client_id='+self.id
        response_type = '&response_type=code'
        scope_str = '&scope='+self.scope
        state_str = '&state='+self.state
        redir = '&redirect_uri='+self.uri

        print("Initializing OAuth2 ...")
        webbrowser.open(URL_AUTH+client_str+response_type+scope_str+state_str+redir)

        # Start the async loop
        print("Waiting for approval ...")
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

    def _get_stash_raw(self, league):
        stashes = API_STASH+league
        return requests.get(stashes, headers=self.headers)
    
    def get_stash(self, league="standard") -> dict:
        return json.loads(self._get_stash_raw(league).content)

    def _get_profile_raw(self):
        return requests.get(API_CHARACTER, headers=self.headers)

    def get_profile(self):
        return json.loads(self._get_profile_raw().content)

    def stash_tab_names(self, league="Standard", filter_remove_only=True) -> list:
        stashes = self.get_stash(league)
        # scrap stash names
        temp=[i["name"] for i in stashes["stashes"]]
        # process names and remove the "remove-only"
        if filter_remove_only:
            count = len(temp)
            for i in range(count):
                ii = count - i -1
                if "Remove-only" in temp[ii]:
                    temp.remove(temp[ii])
        return temp

    def _parse_names(self, depth=DEPTH_ITEMS, stash_dict=None):
        """Parse separately so that we don't fetch for every ques """
        if not stash_dict:
            stash_dict = self.get_stash()
