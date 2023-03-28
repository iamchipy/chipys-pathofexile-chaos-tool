import json
import requests

WEAPON_LIST = ["Sword", "Axe", "Dagger", "Staff", "Bow", "Wand", "Mace"]
def slot_sub(key,value):
    if any(item in value for item in WEAPON_LIST):
        value = "Weapon"
    return [key,value]

print("Fetching basetype info . . .",end=" ")
item_base_types_url = "https://raw.githubusercontent.com/brather1ng/RePoE/master/RePoE/data/base_items.json"
r = requests.get(item_base_types_url)
base_type_dict = dict(json.loads(r.content))
BASE_TYPES = dict([[base_type_dict[base_type]["name"],base_type_dict[base_type]["item_class"]] for base_type in base_type_dict if base_type_dict[base_type]["domain"] == "item"])
SLOT_LOOKUP = dict([slot_sub(k,v) for k,v in BASE_TYPES.items()])
print("done")


if __name__ == "__main__":
    
    print(SLOT_LOOKUP)
