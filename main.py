
import poe_oauth
import info

class StashSearching():
    pass

authentication = poe_oauth.PoeApiHandler(client_id=info.CLIENT_ID,
                                         client_secret=info.CLIENT_SECRET,
                                         scope=info.SCOPE,
                                         uri=info.REDIRECT_URI,
                                        #  manual_token=info.DEV_TOKEN
                                        )

print(authentication.stash_tab_names("hardcore"))
print(authentication.stash_tab_names())

# authenticate 
## check for timeout
# fetch stash data
## filter stash data
### give read out GUI


