import requests
import os
from PIL import Image
from io import BytesIO

import json

from pyrez.api import PaladinsAPI

file_name = "token"
# Gets ID and KEY from a file
with open(file_name, 'r') as f:
    TOKEN = f.readline().strip()    # Does nothing
    PREFIX = f.readline()           # Does nothing
    ID = int(f.readline())
    KEY = f.readline()
f.close()


DAMAGES = ["Cassie", "Kinessa", "Drogoz", "Bomb King", "Viktor", "Sha Lin", "Tyra", "Willo", "Lian", "Strix",
           "Vivian", "Dredge", "Imani"]
FLANKS = ["Skye", "Buck", "Evie", "Androxus", "Maeve", "Lex", "Zhin", "Talus", "Moji", "Koga"]
TANKS = ["Barik", "Fernando", "Ruckus", "Makoa", "Torvald", "Inara", "Ash", "Terminus", "Khan", "Atlas"]
SUPPORTS = ["Grohk", "Grover", "Ying", "Mal Damba", "Seris", "Jenos", "Furia", "Pip", "Io"]

all_champs = DAMAGES + FLANKS + TANKS + SUPPORTS


# Saves image from URL into a folder
def save_image(image_url, folder, name):
    response = requests.get(image_url)
    try:
        image = Image.open(BytesIO(response.content))
        # x, y = image.size
        # if x != 512 and y != 512:
        #    print("Had to resize image for {}.".format(name))
        #    image = image.resize((512, 512), Image.ANTIALIAS)
        path = "{}/{}.png".format(folder, name)
        exists = os.path.isfile(path)
        if not exists:
            image.save(path, "PNG")
    except OSError:
        print("Could not save {} as an image.".format(name))


def save_champ_icons(name):
    champ_icon = "https://web2.hirez.com/paladins/champion-icons/{}.jpg".format(name)
    save_image(champ_icon, "champ_icons", name)
    print("Fetched champion icon for: ", name)


def save_champ_headers(name):
    champ_header = "https://web2.hirez.com/paladins/champion-headers/{}.png".format(name)
    save_image(champ_header, "champ_headers", name)
    print("Fetched champion header for: ", name)


def save_champ_cards(name):
    json_data = requests.get("https://cms.paladins.com/wp-json/wp/v2/champions?slug={}&lang_id=1"
                             .format(name.replace(' ', '-')))

    for card in json_data.json()[0].get("cards"):
        card_name = card.get("card_name_english").lower().replace(' ', '-')
        champ_card = "https://web2.hirez.com/paladins/champion-cards/{}.jpg".format(card_name)
        print(champ_card)
        save_image(champ_card, "champ_cards", card_name)
        print("Fetched champion cards for: {}: {}".format(name, card_name))


def save_card_descriptions(name):
    # paladinsAPI = PaladinsAPI(devId=ID, authKey=KEY)
    # card_description = paladinsAPI.getChampionCards(name, "1")
    # print(card_description)
    english_code = 1
    if "Mal" in name:
        name = "maldamba"
    json_data = requests.get("https://cms.paladins.com/wp-json/wp/v2/champions?slug={}&lang_id={}"
                             .format(name, english_code))

    try:
        json_data = json_data.json()[0].get("cards")
    except (IndexError, json.decoder.JSONDecodeError):
        print("The champion {} does not have any card data.".format(name))
        return None

    champion_card_descriptions = {}
    for card in json_data:
        card_desc = card.get("card_description")
        card_cd = card.get("recharge_seconds")
        card_name = card.get("card_name")
        champion_card_descriptions[card_name] = {'card_desc': card_desc, 'card_cd': card_cd}

    if "mal" in name:
        name = "mal-damba"

    path = "champ_card_desc/{}.json".format(name.lower())
    with open(path, 'w') as json_file:
        json.dump(champion_card_descriptions, json_file)
        print("Fetched champion card descriptions for:", name)


for champ in all_champs:
    champ_name = champ.replace(' ', '-')

    # save_champ_icons(champ_name)
    # save_champ_headers(champ_name)
    # save_champ_cards(champ_name)
    # save_card_descriptions(name=champ_name)


new_champ = "io"
save_champ_cards(new_champ)
# save_champ_icons(new_champ)
# save_champ_headers(new_champ)

# response = requests.get("https://c-3sux78kvnkay76x24mgskvkjogx2eiax78ykijtx2eius.g00.gamepedia.com/g00/3_"
#                                "c-3vgrgjoty.mgskvkjog.ius_/c-3SUXKVNKAY76x24nzzvyx3ax2fx2fmgskvkjog.iax78ykijt."
#                                "iusx2fvgrgjoty_mgskvkjogx2flx2fl1x2fIuurjuct_Oiut."
#                                "vtmx3fbkx78youtx3d53lijk999h1kll086lg16j7kjh186821x26o76i.sgx78qx3dosgmk_$/$/$/$/$")
# cool_down_icon = Image.open(BytesIO(response.content)).convert("RGBA")
# cool_down_icon.save("cool_down_icon.png", "PNG")

# for i in range(1, 6):
#    url = "https://web2.hirez.com/paladins/cards/frame-{}.png".format(i)
#    save_image(url, "card_frames", i)
