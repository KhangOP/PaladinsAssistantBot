from bs4 import BeautifulSoup, SoupStrainer
import requests
import os
from PIL import Image
from io import BytesIO

import json

from colorama import Fore, init
init(autoreset=True)


DAMAGES = ["Cassie", "Kinessa", "Drogoz", "Bomb King", "Viktor", "Sha Lin", "Tyra", "Willo", "Lian", "Strix",
           "Vivian", "Dredge", "Imani"]
FLANKS = ["Skye", "Buck", "Evie", "Androxus", "Maeve", "Lex", "Zhin", "Talus", "Moji", "Koga"]
TANKS = ["Barik", "Fernando", "Ruckus", "Makoa", "Torvald", "Inara", "Ash", "Terminus", "Khan", "Atlas"]
SUPPORTS = ["Grohk", "Grover", "Ying", "Mal'Damba", "Seris", "Jenos", "Furia", "Pip", "Io"]

all_champs = DAMAGES + FLANKS + TANKS + SUPPORTS

languages = [1, 2, 3, 5, 7, 9, 10, 11, 12, 13]


# Converts the language to prefix
def convert_language(x):
    return {
        1: "en",    # English
        2: "de",    # German
        3: "fr",    # French
        5: "zh",    # Chinese
        7: "od",    # Out-dated/Unused
        9: "es",    # Spanish
        10: "pt",   # Portuguese
        11: "ru",   # Russian
        12: "pl",   # Polish
        13: "tr",   # Turkish
    }.get(x, "unknown")  # Return unknown by default if an unknown number is entered


def get_image_paladins_wiki(champion_name, card_image_name):
    url = "https://paladins.gamepedia.com/" + champion_name

    # Print the whole page
    # getpage = requests.get(url=url)
    # getpage_soup = BeautifulSoup(getpage.text, 'html.parser')
    # print(getpage_soup)

    r = requests.get(url)
    c = r.content
    soup = BeautifulSoup(c, 'html.parser')
    # tags = soup.findAll('img')
    card_image_name = card_image_name.replace("-", " ").title()
    card_image_name = "Card {}.png".format(card_image_name)
    print(card_image_name)
    image_data = soup.find('img', alt=card_image_name)
    try:
        image_url = image_data['src']
        image_url = image_url.split(".png")[0].replace("/thumb", "") + ".png"
    except TypeError:
        print(card_image_name)
        image_url = ""

    return image_url


# Saves image from URL into a folder
def save_image(image_url, folder, name):
    response = requests.get(image_url)
    try:
        image = Image.open(BytesIO(response.content))
        # x, y = image.size
        # if x != 512 and y != 512:
        #    print("Had to resize image for {}.".format(name))
        #    image = image.resize((512, 512), Image.ANTIALIAS)

        # Create a folder for the champion
        if not os.path.exists(folder):
            os.makedirs(folder)

        path = "{}/{}.png".format(folder, name)
        exists = os.path.isfile(path)
        if not exists:
            image.save(path, "PNG")
            print(Fore.MAGENTA + "Saved {} as an image.".format(name))
        else:
            print(Fore.YELLOW + "Already have an image saved for {}.".format(name))
        return True
    except OSError:
        print(Fore.RED + "Could not save {} as an image: {}".format(name, image_url))
        return False


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
        card_name = card.get("card_name_english").lower().replace(' ', '-').replace("'", "")
        champ_card = "https://web2.hirez.com/paladins/champion-cards/{}.jpg".format(card_name)
        # print(champ_card)
        champion_name = name.title()
        status = save_image(champ_card, "champ_cards/{}".format(champion_name), card_name)
        if status:
            print("Fetched champion cards for: {}: {}".format(name, card_name))
        else:
            print("Trying to get image from gamepedia.")
            new_url = get_image_paladins_wiki(champion_name, card_name)
            if new_url != "":
                save_image(new_url, "champ_cards/{}".format(champion_name), card_name)


def save_card_descriptions(name):
    champion_card_descriptions = {}
    for lang_num in languages:
        lang = convert_language(lang_num)
        if "Mal" in name:
            name = "maldamba"

        data_url = "https://cms.paladins.com/wp-json/wp/v2/champions?slug={}&lang_id={}".format(name, lang_num)
        json_data = requests.get(url=data_url)

        try:
            json_data = json_data.json()[0].get("cards")
        except (IndexError, json.decoder.JSONDecodeError):
            print("The champion {} does not have any card data.".format(name))
            return None

        champion_card_descriptions[lang] = {}
        for card in json_data:
            card_desc = card.get("card_description")
            card_cd = card.get("recharge_seconds")
            card_name = card.get("card_name")
            card_name_en = card.get("card_name_english")
            champion_card_descriptions[lang][card_name] = {'card_desc': card_desc, 'card_cd': card_cd,
                                                           'card_name_en': card_name_en}

        if "mal" in name:
            name = "mal-damba"

        path = "champ_card_desc_lang/{}.json".format(name.lower())
        with open(path, 'w') as json_file:
            json.dump(champion_card_descriptions, json_file)
            print("Fetched champion card descriptions for: ", name, lang)


# get_image_paladins_wiki("Io", "broken-deity")

# new_champ = "IO"
# save_champ_cards(new_champ)

# save_image("https://gamepedia.cursecdn.com/paladins_gamepedia/b/be/Card_Celestial_Body.png", "testing", "io-asd")

for champ in all_champs:
    champ_name = champ.replace(' ', '-')

    # save_champ_icons(champ_name)
    # save_champ_headers(champ_name)
    save_champ_cards(champ_name)
    save_card_descriptions(name=champ_name)

# new_champ = "raum"
# save_champ_cards(new_champ)     # not ready yet
# save_champ_icons(new_champ)
# save_champ_headers(new_champ)
# save_card_descriptions(new_champ)   # not ready yet

# for i in range(1, 6):
#    url = "https://web2.hirez.com/paladins/cards/frame-{}.png".format(i)
#    save_image(url, "card_frames", i)
