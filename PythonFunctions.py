import random
import requests
from bs4 import BeautifulSoup

import json

from pyrez.api import PaladinsAPI


file_name = "token"
# Gets ID and KEY from a file
with open(file_name, 'r') as f:
    TOKEN = f.readline().strip()  # Does nothing
    ID = int(f.readline())
    KEY = f.readline()
f.close()


paladinsAPI = PaladinsAPI(devId=ID, authKey=KEY)

# List of Champs by Class
DAMAGES = ["Cassie", "Kinessa", "Drogoz", "Bomb King", "Viktor", "Sha Lin", "Tyra", "Willo", "Lian", "Strix", "Vivian",
           "Dredge", "Imani"]
FLANKS = ["Skye", "Buck", "Evie", "Androxus", "Meave", "Lex", "Zhin", "Talus", "Moji", "Koga"]
FRONTLINES = ["Barik", "Fernando", "Ruckus", "Makoa", "Torvald", "Inara", "Ash", "Terminus", "Khan"]
SUPPORTS = ["Grohk", "Grover", "Ying", "Mal'Damba", "Seris", "Jenos", "Furia"]

# Map Names
MAPS = ["Frog Isle", "Jaguar Falls", "Serpent Beach", "Frozen Guard", "Ice Mines", "Ice Mines", "Fish Market",
        "Timber Mill", "Stone Keep", "Brightmarsh", "Splitstone Quarry", "Ascension Peak", "Warder's Gate"]


# Picks a random damage champion.
def pick_damage():
    secure_random = random.SystemRandom()
    return secure_random.choice(DAMAGES)


# Picks a random flank champion.
def pick_flank():
    secure_random = random.SystemRandom()
    return secure_random.choice(FLANKS)


# Picks a random tank champion.
def pick_tank():
    secure_random = random.SystemRandom()
    return secure_random.choice(FRONTLINES)


# Picks a random support champion.
def pick_support():
    secure_random = random.SystemRandom()
    return secure_random.choice(SUPPORTS)


# Picks a random Siege/Ranked map.
def pick_map():
    secure_random = random.SystemRandom()
    return secure_random.choice(MAPS)


# Picks a random champion from any class.
def pick_random_champ():
    secure_random = random.SystemRandom()
    return secure_random.choice([pick_damage, pick_support, pick_tank, pick_flank])()


# Uses the random functions about to generate team of random champions
# It will always pick (1 Damage, 1 Flank, 1 Support, and 1 FrontLine, and then one other champion.)
def gen_team():
    team = [pick_damage(), pick_flank(), pick_support(), pick_tank()]

    fill = pick_random_champ()
    """Keep Generating a random champ until its not one we already have"""
    while fill in team:
        fill = pick_random_champ()

    team.append(fill)

    """Shuffle the team so people get different roles"""
    random.shuffle(team)
    random.shuffle(team)
    random.shuffle(team)

    team_string = "\n"
    for champ in team:
        team_string += champ + "\n"
    return team_string


# Paladins API Code ----------------------------------------------------------------------------------------------------

# n1 = wins and n2 = total matches
def create_win_rate(n1, n2):
    if n2 == 0:  # This means they have no data for the ranked split/season
        return "0"
    return str('{0:.2f}'.format((n1 / n2) * 100))


# Converts the number to the proper name
def convert_rank(x):
    return {
        1: "Bronze 5",
        2: "Bronze 4",
        3: "Bronze 3",
        4: "Bronze 2",
        5: "Bronze 1",
        6: "Silver 5",
        7: "Silver 4",
        8: "Silver 3",
        9: "Silver 2",
        10: "Silver 1",
        11: "Gold 5",
        12: "Gold 4",
        13: "Gold 3",
        14: "Gold 2",
        15: "Gold 1",
        16: "Platinum 5",
        17: "Platinum 4",
        18: "Platinum 3",
        19: "Platinum 2",
        20: "Platinum 1",
        21: "Diamond 5",
        22: "Diamond 4",
        23: "Diamond 3",
        24: "Diamond 2",
        25: "Diamond 1",
        26: "Master",
        27: "GrandMaster",
    }.get(x, "Un-Ranked")


# Player stats
def get_player_stats_api(player_name):
    # Player level, played hours, etc
    try:
        info = paladinsAPI.getPlayer(player_name)
    except:
        return "Player not found. Capitalization does not matter."

    json_data = str(info).replace("'", "\"").replace("None", "0")

    # Works amazingly
    j = json.loads(json_data)
    ss = ""

    # Basic Stats
    ss += "Casual stats: \n"
    ss += "Name: " + (j["Name"]) + "\n"
    ss += "Account Level: " + str(j["Level"]) + "\n"
    total = int(j["Wins"]) + int(j["Losses"])
    ss += "WinRate: " + create_win_rate(int(j["Wins"]), total) + "% out of " + str(total) + \
          " matches.\n"
    ss += "Times Deserted: " + str(j["Leaves"]) + "\n\n"

    # Ranked Info
    ss += "Ranked stats for Season " + str(j["RankedKBM"]["Season"]) + ":\n"
    # Rank (Masters, GM, Diamond, etc)
    ss += "Rank: " + convert_rank(j["RankedKBM"]["Tier"]) + "\nTP: " + str(j["RankedKBM"]["Points"]) + " Position: " +\
          str(j["RankedKBM"]["Rank"]) + "\n"

    win = int(j["RankedKBM"]["Wins"])
    lose = int(j["RankedKBM"]["Losses"])

    ss += "WinRate: " + create_win_rate(win, win + lose) + "% (" + '{}-{}'.format(win, lose) + ")\n"
    ss += "Times Deserted: " + str(j["RankedKBM"]["Leaves"]) + "\n\n"

    # Extra info
    ss += "Extra details: \n"
    ss += "Account created on: " + str(j["Created_Datetime"]).split()[0] + "\n"
    ss += "Last login on: " + str(j["Last_Login_Datetime"]).split()[0] + "\n"
    ss += "Platform: " + str(j["Platform"]) + "\n"
    ss += "MasteryLevel: " + str(j["MasteryLevel"]) + "\n"
    ss += "Steam Achievements completed: " + str(j["Total_Achievements"]) + "/58\n"

    return ss


def get_champ_stats_api(player_name, champ):
    # Stats for the champs
    champ = str(champ).lower().capitalize()
    # Will Fix Later !!!
    player = paladinsAPI.getPlayer(player_name)
    stats = paladinsAPI.getChampionRanks(player.playerId)

    if "Mal" in champ:
        champ = "Mal'Damba"

    ss = ""

    for stat in stats:
        json_data = str(stat).replace("'", "\"").replace("None", "0").replace("Mal\"", "Mal\'")
        j = json.loads(json_data)
        wins = stat.wins
        loses = stat.losses
        kda = stat.getKDA()
        if stat.godName == champ:
            ss = str('Champion: {} (Lv {})\nKDA: {} ({}-{}-{}) \nWinRate: {}% ({}-{}) \nLast Played: {}')
            ss = ss.format(stat.godName, stat.godLevel, kda, stat.kills, stat.deaths, stat.assists,
                           create_win_rate(wins, wins+loses), stat.wins, stat.losses, str(j["LastPlayed"]).split()[0])
        # They have not played this champion yet
        if ss == "":
            ss += "No data for champion: " + champ + "\n"

    return ss


def create_json(raw_data):
    json_data = str(raw_data).replace("'", "\"").replace("None", "0").replace("Mal\"", "Mal\'")
    return json.loads(json_data)


# Gets kda and Winrate for a player
def get_global_kda(player_name):
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
        # error = "Could not the find player " + player_name + \
        #       ". Please make sure the name is spelled right (capitalization does not matter)."
        error = [player_name, "???", "???", "???"]
        return error

    # Puts all the info into one string to print
    # global_stats = "Name: " + stats.pop(0) + " (Lv. " + stats.pop(0) + ")\n" + "WinRate: " + \
    #                stats.pop(0) + "\n" + "Global KDA: " + stats.pop(0)
    # return global_stats
    return stats


def get_player_in_match(player_name):
    # Data Format
    # {'Match': 795950194, 'match_queue_id': 452, 'personal_status_message': 0, 'ret_msg': 0, 'status': 3,
    # 'status_string': 'In Game'}

    # Will Fix Later !!!
    player = paladinsAPI.getPlayer(player_name)
    j = create_json(paladinsAPI.getPlayerStatus(player.playerId))
    if j == 0:
        return str("Player " + player_name + " is not found.")
    match_id = j["Match"]
    if j['status'] == 0:
        return "Player is offline."
    elif j['status'] == 1:
        return "Player is in lobby."
    elif j['status'] == 2:
        return "Player in champion selection."
    # Need to test for champ banning and selection
    # print(match_id)

    # ValueError: 2509 is not a valid Champions (Imani)

    # match_queue_id = 424 = Siege
    # match_queue_id = 445 = Test Maps (NoneType) --> no json data
    # match_queue_id = 452 = Onslaught
    # match_queue_id = 469 = DTM
    # match_queue_id = 486 = Ranked (Invalid)

    match_string = "Unknown match Type"
    if j["match_queue_id"] == 424:
        match_string = "Siege"
    elif j["match_queue_id"] == 445:
        return "No data for Test Maps."
    elif j["match_queue_id"] == 452:
        match_string = "Onslaught"
    elif j["match_queue_id"] == 469:
        match_string = "Team Death Match"
    elif j["match_queue_id"] == 486:
        return "Ranked is currently not working."

    # Data Format
    # {'Account_Level': 17, 'ChampionId': 2493, 'ChampionName': 'Koga', 'Mastery_Level': 10, 'Match': 795511902,
    # 'Queue': '424', 'SkinId': 0, 'Tier': 0, 'playerCreated': '11/10/2017 10:00:03 PM', 'playerId': '12368291',
    # 'playerName': 'NabbitOW', 'ret_msg': None, 'taskForce': 1, 'tierLosses': 0, 'tierWins': 0}
    try:
        players = paladinsAPI.getMatchPlayerDetails(match_id)
    except:
        return "Imani is in the match and therefore we can not get stats on the current Match."
    # print(players)
    info = []
    team1 = []
    team2 = []
    for player in players:
        j = create_json(player)
        name = (j["playerName"])
        if (j["taskForce"]) == 1:
            team1.append(name)
        else:
            team2.append(name)

    match_data = ""
    match_data += player_name + " is in a " + match_string + " match."  # Match Type
    #print(match_data)
    match_data += str('\n\n{:18} {:7}  {:7}  {:6}\n\n').format("Player name", "Level", "WinRate", "KDA")

    for player in team1:
        # print(get_global_kda(player))
        pl = get_global_kda(player)
        ss = str('{:18} Lv. {:3}  {:7}  {:6}\n')
        match_data += ss.format(pl.pop(0), pl.pop(0), pl.pop(0), pl.pop(0))

    match_data += "\n"

    for player in team2:
        # print(get_global_kda(player))
        info.append(get_global_kda(player))
        pl = get_global_kda(player)
        ss = str('{:18} Lv. {:3}  {:7}  {:6}\n')
        match_data += ss.format(pl.pop(0), pl.pop(0), pl.pop(0), pl.pop(0))

    return match_data


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


def get_champ_stats(player_name, champ):
    player_name = str(player_name)
    champ = str(champ).lower().capitalize()

    # Personal stats
    if champ == "Me":
        # return get_global_stats(player_name)
        return get_player_stats_api(player_name)

    # Personal stats
    if champ == "Elo":
        return get_player_elo(player_name)

    return get_champ_stats_api(player_name, champ)


"""End of Python Functions"""
