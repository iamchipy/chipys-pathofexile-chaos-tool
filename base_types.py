import json
import requests


helm = ['Iron Hat','Cone Helmet','Barbute Helmet','Close Helmet','Gladiator Helmet','Reaver Helmet','Siege Helmet','Samnite Helmet','Ezomyte Burgonet','Royal Burgonet','Eternal Burgonet','Leather Cap','Tricorne','Leather Hood','Wolf Pelt','Hunter Hood','Noble Tricorne','Ursine Pelt','Silken Hood','Sinner Tricorne','Lion Pelt','Vine Circlet','Iron Circlet','Torture Cage','Tribal Circlet','Bone Circlet','Lunaris Circlet','Steel Circlet','Necromancer Circlet','Solaris Circlet','Mind Cage','Hubris Circlet','Battered Helm','Sallet','Sorrow Mask','Visored Sallet','Gilded Sallet','Secutor Helm','Fencer Helm','Atonement Mask','Lacquered Helmet','Fluted Bascinet','Pig-Faced Bascinet','Nightmare Bascinet','Penitent Mask','Rusted Coif','Soldier Helmet','Imp Crown','Great Helmet','Crusader Helmet','Aventail Helmet','Zealot Helmet','Demon Crown','Great Crown','Magistrate Crown','Prophet Crown','Praetor Crown','Bone Helmet','Archdemon Crown','Scare Mask','Plague Mask','Gale Crown','Iron Mask','Festival Mask','Golden Mask','Raven Mask','Callous Mask','Winter Crown','Regicide Mask','Harlequin Mask','Vaal Mask','Deicide Mask','Blizzard Crown']
body = ['Plate Vest','Chestplate','Copper Plate','War Plate','Full Plate','Arena Plate',
        'Lordly Plate','Bronze Plate','Battle Plate','Sun Plate','Colosseum Plate',
        'Majestic Plate','Golden Plate','Crusader Plate','Astral Plate',
        'Gladiator Plate','Glorious Plate','Shabby Jerkin','Strapped Leather',
        'Buckskin Tunic','Wild Leather','Full Leather','Sun Leather',"Thief's Garb",
        'Eelskin Tunic','Frontier Leather','Glorious Leather','Coronal Leather',
        "Cutthroat's Garb",'Sharkskin Tunic','Destiny Leather','Exquisite Leather',
        'Zodiac Leather',"Assassin's Garb",'Simple Robe','Silken Vest',
        "Scholar's Robe",'Silken Garb',"Mage's Vestment",'Silk Robe','Cabalist Regalia',
        "Sage's Robe",'Silken Wrap',"Conjurer's Vestment",'Spidersilk Robe',
        'Destroyer Regalia',"Savant's Robe",'Necromancer Silks',"Occultist's Vestment",
        'Widowsilk Robe','Vaal Regalia','Scale Vest','Light Brigandine','Scale Doublet',
        'Infantry Brigandine','Full Scale Armour',"Soldier's Brigandine",
        'Field Lamellar','Wyrmscale Doublet','Hussar Brigandine','Full Wyrmscale',
        "Commander's Brigandine",'Battle Lamellar','Dragonscale Doublet',
        'Desert Brigandine','Full Dragonscale',"General's Brigandine",
        'Triumphant Lamellar','Chainmail Vest','Chainmail Tunic','Ringmail Coat',
        'Chainmail Doublet','Full Ringmail','Full Chainmail','Holy Chainmail',
        'Latticed Ringmail','Crusader Chainmail','Ornate Ringmail','Chain Hauberk',
        'Devout Chainmail','Loricated Ringmail','Conquest Chainmail','Elegant Ringmail',
        "Saint's Hauberk",'Saintly Chainmail','Padded Vest','Oiled Vest',
        'Padded Jacket','Oiled Coat','Scarlet Raiment','Waxed Garb','Bone Armour',
        'Quilted Jacket','Sleek Coat','Crimson Raiment','Lacquered Garb','Crypt Armour',
        'Sentinel Jacket','Varnished Coat','Blood Raiment','Sadist Garb',
        'Carnal Armour','Grasping Mail','Sacrificial Garb']

print("Fetching basetype info . . .",end=" ")
item_base_types_url = "https://raw.githubusercontent.com/brather1ng/RePoE/master/RePoE/data/base_items.json"
r = requests.get(item_base_types_url)
base_type_dict = dict(json.loads(r.content))
BASE_TYPES = dict([[base_type_dict[base_type]["name"],base_type_dict[base_type]["item_class"]] for base_type in base_type_dict if base_type_dict[base_type]["domain"] == "item"])
print("done")
