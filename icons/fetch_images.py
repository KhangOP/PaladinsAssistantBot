import requests
import os
from PIL import Image
from io import BytesIO

from pyrez.api import PaladinsAPI

file_name = "token"
# Gets ID and KEY from a file
with open(file_name, 'r') as f:
    TOKEN = f.readline().strip()    # Does nothing
    PREFIX = f.readline()           # Does nothing
    ID = int(f.readline())
    KEY = f.readline()
f.close()

champs = ["androxus", "atlas", "ash", "barik", "bomb king", "buck", "cassie", "dredge", "drogoz", "evie", "fernando",
          "furia", "grohk", "grover", "imani", "inara", "jenos", "khan", "kinessa", "koga", "lex", "lian", "maeve",
          "makoa", "maldamba", "moji", "pip", "ruckus", "seris", "sha lin", "skye", "strix", "talus", "terminus",
          "torvald", "tyra", "viktor", "vivian", "willo", "ying", "zhin"]


# Saves image from URL into a folder
def save_image(image_url, folder, name):
    response = requests.get(image_url)
    try:
        image = Image.open(BytesIO(response.content))
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
        save_image(champ_card, "champ_cards", card_name)
        print("Fetched champion cards for: {}: {}".format(name, card_name))


def save_card_descriptions(name):
    paladinsAPI = PaladinsAPI(devId=ID, authKey=KEY)
    card_description = paladinsAPI.getChampionCards(name, "1")
    print(card_description)


for champ in champs:
    champ_name = champ.replace(' ', '-')

    # save_champ_icons(champ_name)
    # save_champ_headers(champ_name)
    # save_champ_cards(champ_name)

print(save_champ_cards("Makoa"))
