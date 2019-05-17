import requests
from PIL import Image
from io import BytesIO

champs = [ "androxus", "atlas", "ash", "barik", "bomb king", "buck", "cassie", "dredge", "drogoz", "evie", "fernando",
           "furia", "grohk", "grover", "imani", "inara", "jenos", "khan", "kinessa", "koga", "lex", "lian", "maeve",
           "makoa", "maldamba", "moji", "pip", "ruckus", "seris", "sha lin", "skye", "strix", "talus", "terminus",
           "torvald", "tyra", "viktor", "vivian", "willo", "ying", "zhin" ]


# Saves image from URL into a folder
def save_image(image_url, folder, name):
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    path = "{}/{}.png".format(folder, name)
    image.save(path, "PNG")


def save_champ_icons(name):
    champ_icon = "https://web2.hirez.com/paladins/champion-icons/{}.jpg".format(name)
    save_image(champ_icon, "champ_icons", name)
    print("Fetched champion icon for: ", name)


def save_champ_headers(name):
    champ_header = "https://web2.hirez.com/paladins/champion-headers/{}.png".format(name)
    save_image(champ_header, "champ_headers", name)
    print("Fetched champion header for: ", name)


for champ in champs:
    champ_name = champ.replace(' ', '-')

    save_champ_icons(champ_name)
    save_champ_headers(champ_name)

    # get and write champHeader on HD
    """
    json_data = requests.get("https://cms.paladins.com/wp-json/wp/v2/champions?slug={}&lang_id=1"
                             .format(champ.replace(' ', '-')))

    for card in json_data.json()[0].get("cards"):
        cardImg = "https://web2.hirez.com/paladins/champion-cards/{}.jpg".format(card.get("card_name_english").lower().replace(' ', '-'))
        # get and write cardImg on HD
    """
