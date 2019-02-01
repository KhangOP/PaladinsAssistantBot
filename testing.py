import requests
from bs4 import BeautifulSoup


# Helper function to the get_player_elo(player_name) function
def return_mode(name):
    mode = ""
    if name == "Siege":
        mode += "Siege rating: \n"
    elif name == "Survival":
        mode += "Survival rating: \n"
    elif name == "Deathmatch":
        mode += "Team Deathmatch rating: \n"
    else:
        mode += "Overall Guru Score: \n"
    return mode


# Elo?
def get_player_elo(player_name):
    url = "http://paladins.guru/profile/pc/" + str(player_name) + "/casual"
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    soup = str(soup.get_text()).split(" ")
    data = list(filter(None, soup))

    stats = ""

    # Gets elo information below
    for i, row in enumerate(data):
        #print(data[i])
        if data[i] == "Siege" or data[i] == "Survival" or data[i] == "Deathmatch" or data[i] == "Score":
            if data[i+1] == "Rank":
                mode = return_mode(data[i])
                mode += str("Rank: " + data[i + 2])             # Rank
                mode += str(" (Top " + data[i + 5] + ")\n")     # Rank %
                mode += str("Elo: " + data[i + 6] + "\n")       # Elo
                mode += str("WinRate: " + data[i + 8])          # WinRate
                mode += str(" (" + data[i + 10] + "-")          # Wins
                mode += data[i + 11] + ")"                      # Loses
                stats += mode + "\n\n"
            elif data[i+1] == "-":
                mode = return_mode(data[i])
                mode += str("Rank: ???")                    # Rank
                mode += str(" (Top " + "???" + ")\n")       # Rank %
                mode += str("Elo: " + data[i + 2] + "\n")   # Elo
                mode += str("WinRate: " + data[i + 4])      # WinRate
                mode += str(" (" + data[i + 6] + "-")       # Wins
                mode += data[i + 7] + ")"                   # Loses
                stats += mode + "\n\n"
        if data[i] == "Siege":
            if data[i+1] == "Normal:":
                break

    return stats


# name = "xxluk3warm"
# name = "BombEthan"
name = "FeistyJalapeno"
#print(get_player_elo(name))


# NOT WORKING FOR NOW
def get_champion_stats(player_name, champ):
    url = "http://paladins.guru/profile/pc/" + str(player_name) + "/champions"
    url = "http://paladins.guru/profile/pc/FeistyJalapeno/champions"
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    soup = str(soup.get_text())
    print(soup)
    #sup = str(soup.get_text())
    #print(sup)


name = "FeistyJalapeno"
champ = "Strix"
# get_champion_stats(name, "")


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

    # Error checking to make sure that the player was found on the site
    if 'not' in stats:
        error = "Could not the find player " + player_name + \
                ". Please make sure the name is spelled right (capitalization does not matter)."
        return str(error)

    # Puts all the info into one string to print
    global_stats = "Name: " + stats.pop(0) + "\n" + "Account Level: " + stats.pop(0) + "\n" + "Wins: " + stats.pop(0) +\
                   "\n" + "Loses: " + stats.pop(0) + "\n" + "WinRate: " + stats.pop(0) + "\n" + "Kills: " + \
                   stats.pop(0) + "\n" + "Deaths: " + stats.pop(0) + "\n" + "Assists: " + stats.pop(0) + "\n" + \
                   "Global KDA: " + stats.pop(0)
    return global_stats


player_name = "feistyjalapeno"
# print(get_global_stats(player_name))


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

    # Error checking to make sure that the player was found on the site
    if "https://mypaladins.com/player" not in url:
        error = "Could not the find player " + player_name + \
                ". Please make sure the name is spelled right (capitalization does not matter)."
        return str(error)

    url = url + "/champions"
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')

    sup = str(soup.get_text()).splitlines()
    data = list(filter(None, sup))

    """
    if champ == "Me":
        print(sup)
        return 1
    """

    yes = 0
    info = []
    matches = 0

    # Gathering the info we want
    for i, row in enumerate(data):
        data[i] = data[i].replace("/", "").strip()
        # print(data[i])
        if data[i] == champ and data[i-1] != "Refresh Data":    # (if player name = champ name they are looking for)
            yes = 1
        if yes >= 1:
            if yes == 3 or yes == 4 or yes == 5:
                pass
            elif yes == 7 or yes == 8:
                matches += int(data[i])
            else:
                info.append(data[i])
            yes += 1
            if yes == 10:
                break

    # Error checking to make sure there is data for the champion they entered
    if not info:
        error = "Could not the find champion " + champ + \
                ". Please make sure the champion name is spelled right (capitalization does not matter)."
        return str(error)

    # Here is what we want
    results = str("Champion: " + info.pop(0) + "\n" + info.pop(0) + "\n" + "KDA: " + info.pop(0) + "\n" + "WinRate: " +
                  info.pop(0) + " out of " + str(matches) + " matches.")
    return results


player_name = "Seris"
champ = "Seris"

print(get_champ_stats(player_name, champ))

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
