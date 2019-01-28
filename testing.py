import requests
from bs4 import BeautifulSoup


def get_global_stats(player_name):
    player_name = str(player_name).lower()
    url = "http://paladins.guru/profile/pc/" + player_name

    soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    sup = str(soup.get_text())

    sup = sup.split(" ")
    data = list(filter(None, sup))

    stats = []

    # Gets account name and level
    for i, row in enumerate(data):
        if data[i] == "Giveaway":
            stats.append(data[i + 2])
            stats.append(data[i + 1])
            break

    # Gets Global wins and loses
    for i, row in enumerate(data):
        if data[i] == "Loss":
            stats.append(data[i + 1])
            stats.append(data[i + 3])
            new_s = str(data[i + 4].replace("(", "") + " %")
            stats.append(new_s)
            break

    # Gets Global KDA
    for i, row in enumerate(data):
        if data[i] == "KDA":
            stats.append(data[i + 1])
            stats.append(data[i + 3])
            stats.append(data[i + 5])
            stats.append(data[i + 6])
            break

    # Puts all the info into one string to print
    global_stats = "Name: " + stats.pop(0) + "\n" + "Account Level: " + stats.pop(0) + "\n" + "Wins: " + stats.pop(0) +\
                   "\n" + "Loses: " + stats.pop(0) + "\n" + "WinRate: " + stats.pop(0) + "\n" + "Kills: " + \
                   stats.pop(0) + "\n" + "Deaths: " + stats.pop(0) + "\n" + "Assists: " + stats.pop(0) + "\n" + \
                   "Global KDA: " + stats.pop(0)
    return global_stats

get_global_stats("feistyjalapeno")


def get_champ_stats(player_name, champ):
    player_name = str(player_name)
    champ = str(champ).lower().capitalize()

    # Special case cause of the way the site stores the champion name
    if "Mal" in champ:
        champ = "Mal'Damba"

    url = "https://mypaladins.com/player/" + player_name
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')

    # Get the secret number assigned to every player on their site
    for link in soup.find_all('a'):
        link = link.get('href')
        if link != "/":
            url = link.replace("pl/", "")
            break

    url = url + "/champions"
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')

    sup = str(soup.get_text()).splitlines()
    sup = list(filter(None, sup))

    """
    if champ == "Me":
        print(sup)
        return 1
    """

    yes = 0
    info = []
    matches = 0

    # Gathering the info we want
    for item in sup:
        item = item.replace("/", "").strip()
        if item == champ:
            yes = 1
        if yes >= 1:
            if yes == 3 or yes == 4 or yes == 5:
                pass
            elif yes == 7 or yes == 8:
                matches += int(item)
            else:
                info.append(item)
            yes += 1
            if yes == 10:
                break

    # Here is what we want
    results = str("Champion: " + info.pop(0) + "\n" + info.pop(0) + "\n" + "KDA: " + info.pop(0) + "\n" + "WinRate: " +
                  info.pop(0) + " out of " + str(matches) + " matches.")
    return results



#player_name = "feistyjalapeno"
#champ = "strix"

#print(get_champ_stats(player_name, champ))

"""
print(soup.prettify())

print(soup.find_all('a'))

print(soup.find_all('div'))
"""


"""
# api-endpoint
URL = "https://mypaladins.com/player/"

playerName = "feistyjalapeno"

# defining a params dict for the parameters to be sent to the API
PARAMS = {'tabindex':1,
          'type':"search",
           'class':"js-txt-search-player form-control",
            'name': playerName}

# sending get request and saving the response as response object
r = requests.get(url=URL, params=PARAMS)

print(r)

# extracting data in json format
data = r.json()
print(data)
"""
