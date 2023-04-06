import json
import requests

# announce start
print("Fetching basetype info . . .",end=" ")

# base weapons names 
WEAPON_LIST = ["Sword", "Axe", "Dagger", "Staff", "Bow", "Wand", "Mace"]
ITEM_BASE_TYPES_URL = "https://raw.githubusercontent.com/brather1ng/RePoE/master/RePoE/data/base_items.json"

# combind slots for all weapon types to have a single slot "weapons"
def slot_sub(key,value):
    if any(item in value for item in WEAPON_LIST):
        value = "Weapon"
    return [key,value]

# fetch basetypes
r = requests.get(ITEM_BASE_TYPES_URL)
base_type_dict = dict(json.loads(r.content))

# concat into list of basetype&class
BASE_TYPES = dict([[base_type_dict[base_type]["name"],base_type_dict[base_type]["item_class"]] for base_type in base_type_dict if base_type_dict[base_type]["domain"] == "item"])

# build slot list
SLOT_LOOKUP = dict([slot_sub(k,v) for k,v in BASE_TYPES.items()])

# TODO reduce excess string check by narrowing down this list 
"""Body Armour"""
WEAPON_CLASSES = [v for v in BASE_TYPES.items() if any(item in v for item in WEAPON_LIST)]

print("done")

if __name__ == "__main__":
    # print(SLOT_LOOKUP)
    # print(base_type_dict)
    print(WEAPON_CLASSES)
