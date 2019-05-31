import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pytz import timezone

import time


# Est Time zone for logging function calls
def get_est_time():
    return datetime.now(timezone('EST')).strftime("%H:%M:%S %Y/%m/%d")


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
# name = "ggggraaaahhhhh"
# print(get_player_elo(name))


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


# Gets global stats for a player
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


# player_name = "feistyjalapeno"
# print(get_global_stats(player_name))


# Gets kda and Winrate for a player
def get_global_kda(player_name):
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
            new_s = str(data[i + 4].replace("(", "") + " %")
            stats.append(new_s)
            break

    # Gets Global KDA
    for i, row in enumerate(data):
        if data[i] == "KDA":
            stats.append(data[i + 6])
            break

    # Error checking to make sure that the player was found on the site
    if 'not' in stats:
        error = "Could not the find player " + player_name + \
                ". Please make sure the name is spelled right (capitalization does not matter)."
        return str(error)

    # Puts all the info into one string to print
    # global_stats = "Name: " + stats.pop(0) + " (Lv. " + stats.pop(0) + ")\n" + "WinRate: " + \
    #                stats.pop(0) + "\n" + "Global KDA: " + stats.pop(0)
    # return global_stats
    return stats


# player_name = "feistyjalapeno"
# print(get_global_kda(player_name))


# Calculates the kda
def cal_kda(kills, deaths, assists):
    if assists == 0:  # Could happen
        assists = 1
    if deaths == 0:  # Prefect KDA
        return str(kills + (assists/2))
    return str('{0:.2f}'.format(float(kills + (assists/2))/deaths))


# n1 = wins and n2 = total matches
def create_win_rate(n1, n2):
    if n2 == 0:  # This means they have no data for the ranked split/season
        return "0"
    return str('{0:.2f}'.format((n1 / n2) * 100))


# Gets stats for a champ from the my paladins site
def get_champ_stats_my_paladins(player_name, champ):
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
        ss = str('*{:18} Lv. {:3}  {:7}  {:6}\n')
        ss = ss.format(champ, "???", "???", "???")
        return ss

    #################
    # UMMMMM
    check_url = url.replace(".com/", ".com/api/") + "checkdata"
    soup = BeautifulSoup(requests.get(check_url).text, 'html.parser')
    print("New data: ", soup)

    # Force the site to refresh?
    data_url = url + "refresh"
    print(data_url)
    soup = BeautifulSoup(requests.get(data_url).text, 'html.parser')

    time.sleep(4)  # Wait for the site to refresh
    #################

    url = url + "/champions"
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')

    sup = str(soup.get_text()).splitlines()
    data = list(filter(None, sup))

    """
    if champ == "Me":
        print(sup)
        return 1
    """

    yes, wins, loses, kills, deaths, assists = 0, 0, 0, 0, 0, 0
    info = []

    # Gathering the info we want
    for i, row in enumerate(data):
        data[i] = data[i].replace("/", "").strip()
        # print(data[i])
        if data[i] == champ and data[i-1] != "Refresh Data":    # (if player name = champ name they are looking for)
            yes = 1
        if yes >= 1:
            if yes == 3:
                kills = int(data[i])
            if yes == 4:
                deaths = int(data[i])
            if yes == 5:
                assists = int(data[i])
            elif yes == 7 or yes == 8:
                if data[i] == "":  # Missing data on the site
                    info.append("???")
                    break
                else:
                    if yes == 7:
                        wins = int(data[i])
                    else:
                        loses = int(data[i])
            else:
                info.append(data[i])
            yes += 1
            if yes == 10:
                break

    # Error checking to make sure there is data for the champion they entered
    if not info:
        error = "Could not the find champion " + champ + \
                ". Please make sure the champion name is spelled right (capitalization does not matter)."
        ss = str('*{:18} Lv. {:3}  {:7}  {:6}\n')
        ss = ss.format(champ, "???", "???", "???")
        return ss

    # Here is what we want
    ss = str('*{:18} Lv. {:3}  {:7}  {:6}\n')
    win_rate = create_win_rate(wins, wins+loses)
    win_rate += " %"
    level = info[1].replace("Level", "").strip()
    kda = cal_kda(kills, deaths, assists)
    kda = "(" + kda + ")"
    ss = ss.format(champ, str(level), win_rate, kda)
    """This Block of code adds color based on WinRate"""
    if "???" in win_rate:
        pass
    elif (float(win_rate.replace(" %", ""))) > 55.00:
        ss = ss.replace("*", "+")
    elif (float(win_rate.replace(" %", ""))) < 50.00:
        ss = ss.replace("*", "-")
    """^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"""
    return ss


player_name = "Frosho"
champ = "barik"

print(get_champ_stats_my_paladins(player_name, champ))

'''
@client.command(name='placeholder',
                pass_context=True,
                aliases=['t'])
async def placeholder(ctx):
    """
    embed = discord.Embed(
        colour=discord.colour.Color.dark_teal()
    )
    embed.add_field(name="image", value="http://paladins.guru/assets/img/champions/maldamba.jpg", inline=False)
    await client.say(embed=embed)
    """
    author = ctx.message.author

    embed = discord.Embed(
        colour=discord.colour.Color.dark_teal()
    )
    embed.add_field(name='Player 1', value="http://paladins.guru/assets/img/champions/grohk.jpg", inline=True)
    embed.add_field(name='Player 2', value="<:yinglove:544651722371366924>", inline=True)
    embed.add_field(name='Player 3', value="<:yinglove:544651722371366924>", inline=True)
    embed.add_field(name='Player 4', value="<:yinglove:544651722371366924>", inline=True)
    embed.add_field(name='Player 5', value="<:yinglove:544651722371366924>", inline=True)

    await client.send_message(author, embed=embed)

    embed = discord.Embed(
        colour=discord.colour.Color.dark_gold()
    )
    embed.set_image(url="http://paladins.guru/assets/img/champions/grohk.jpg")
    embed.set_image(url="http://paladins.guru/assets/img/champions/lian.jpg")
    # embed.set_image(url="asd.png") does not work
    await client.send_message(author, embed=embed)

    # file = discord.File("asd.png", file_name="asd.png")
    await client.send_file(author, "asd.png")

    await client.say("<:yinglove:544651722371366924>     <:yinglove:544651722371366924> <:yinglove:544651722371366924> "
                     "<:yinglove:544651722371366924>     <:yinglove:544651722371366924>")
'''


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
