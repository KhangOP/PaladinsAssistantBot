import requests
from pyrez.api import PaladinsAPI
from datetime import timedelta, datetime
import json
import time
"""
ResponseFormat = "JSON"

api_url = "http://api.paladins.com/paladinsapi.svc"


def createTimeStamp(format="%Y%m%d%H%M%S"):
    return currentTime().strftime(format)


def currentTime():
    return datetime.utcnow()

paladinsAPI.__createSession__()
SessionId = paladinsAPI.currentSessionId
Signature = (paladinsAPI.__createSignature__("createsession"))

print(Signature)

url = str(api_url + "/getplayerjson/" + "3046/" + Signature + "/" + SessionId + "/" + createTimeStamp() + "/" + "FeistyJalapeno")
print(url)

r = requests.get(url)
print(r.status_code)
print(r.json())
"""


# n1 = wins and n2 = total matches
def create_win_rate(n1, n2):
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


paladinsAPI = PaladinsAPI(devId=3046, authKey="BB8E882EADB0431E990CD95E05C2B8C9")
print(paladinsAPI.getDataUsed())


def get_player_stats(player_name):
    # Player level, played hours, etc
    try:
        info = paladinsAPI.getPlayer(player_name)
    except:
        return "Player not found. Capitalization does not matter."
    # print(info)

    json_data = str(info).replace("'", "\"").replace("None", "0")
    #print(json_data)

    # Works amazingly
    j = json.loads(json_data)
    ss = ""
    # print(str(j["Last_Login_Datetime"]).split()[0], j["RankedKBM"]["Tier"])

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
    ss += "Steam Achievements completed: " + str(j["Total_Achievements"]) + "\n"

    return ss


# print(get_player_stats("fEistyjalapeNO"))


def get_champ_stats_api(player_name, champ):
    # Stats for the champs
    champ = str(champ).lower().capitalize()
    stats = paladinsAPI.getChampionRanks(player_name)

    if "Mal" in champ:
        champ = "Mal'Damba"

    ss = ""
    t_wins = 0
    t_loses = 0
    t_kda = 0
    count = 0

    for stat in stats:
        # print(type(stat))
        # print(type(str(stat)))
        json_data = str(stat).replace("'", "\"").replace("None", "0").replace("Mal\"", "Mal\'")
        #print(json_data)
        j = json.loads(json_data)
        wins = stat.wins
        loses = stat.losses
        kda = stat.getKDA()
        count += 1
        if stat.godName == champ:
            ss = str('Champion: {} (Lv {})\nKDA: {} ({}-{}-{}) \nWinRate: {}% ({}-{}) \nLast Played: {}')
            ss = ss.format(stat.godName, stat.godLevel, kda, stat.kills, stat.deaths, stat.assists,
                           create_win_rate(wins, wins+loses), stat.wins, stat.losses, str(j["LastPlayed"]).split()[0])
        t_wins += wins
        t_loses += loses
        t_kda += kda
        # print(stat.getKDA())
        # print(stat.godName)

    global_ss = str("\n\nGlobal KDA: {}\nGlobal WinRate: {}%")
    win_rate = create_win_rate(t_wins, t_wins + t_loses)
    t_kda = str('{0:.2f}').format(t_kda/count)
    global_ss = global_ss.format(t_kda, win_rate)
    ss += global_ss
    return ss


print(get_champ_stats_api("FeistyJalapeno", "makoa"))

# IS the person offline
# status = paladinsAPI.getPlayerStatus("FeistyJalapeno")
# print(status)

"""
# Get match info
matches = paladinsAPI.getMatchHistory("FeistyJalapeno")
for match in matches:
    print(match)
"""


# http://api.smitegame.com/smiteapi.svc/createsessionJson/1004/8f53249be0922c94720834771ad43f0f/20120927183145

# for some in info:
#    print()


# print(championsRank)


'''
if championsRank is not None:
    for championRank in championsRank:
        print(championRank.getWinratio())
        
'''
