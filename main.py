
import poe_oauth
import private

class StashSearching():
    pass

authentication = poe_oauth.PoeApiHandler(client_id=private.CLIENT_ID,
                                         client_secret=private.CLIENT_SECRET,
                                         scope=private.SCOPE,
                                         uri=private.REDIRECT_URI,
                                         manual_token=private.DEV_TOKEN
                                        )

print(authentication.stash_tab_names("hardcore"))
print(authentication.stash_tab_names())
# print(authentication.stash_tab_names("hardcore/$"))

# authenticate 
## check for timeout
# fetch stash data
## filter stash data
### give read out GUI


