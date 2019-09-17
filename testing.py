from pyrez.api import PaladinsAPI
import json

file_name = "token"
# Gets ID and KEY from a file
with open(file_name, 'r') as f:
    TOKEN = f.readline().strip()    # Does nothing
    PREFIX = f.readline()           # Does nothing
    ID = int(f.readline())
    KEY = f.readline()
f.close()

paladinsAPI = PaladinsAPI(devId=ID, authKey=KEY)

"""
try:
    player = paladinsAPI.getPlayer("Bubbles")
    print(player)
    player = paladinsAPI.getPlayerId("Bubbles", "22")
    player = paladinsAPI.getPlayer(player[0].playerId)
    print(player)
except BaseException:
    print("could not find")
"""


def get_player_id(player_name):
    if str(player_name).isnumeric():
        return player_name
    with open("player_ids") as json_f:
        player_ids = json.load(json_f)

    # This player is already in the dictionary and therefor we don't need to waste an api call to get the player id.
    if player_name in player_ids:
        return player_ids[player_name]
    else:
        try:
            original_name = player_name
            if "\"" not in player_name:
                player = paladinsAPI.getPlayer(player_name)
            else:  # Console name
                player_name, platform = player_name.replace('\"', "").rsplit(' ', 1)
                players = paladinsAPI.searchPlayers(player_name)

                platform = platform.lower()
                if platform == "xbox":
                    platform = "10"
                elif platform == "ps4":
                    platform = "9"
                elif platform == "switch":
                    platform = "22"
                else:
                    # ```md\nInvalid platform name. Valid platform names are:\n1. Xbox\n2. PS4\n3. Switch```
                    return -2

                players = [player for player in players if player.playerName.lower() == player_name.lower() and
                           player['portal_id'] == platform]
                num_players = len(players)
                if num_players > 1:
                    return -3  # too many names (name overlap in switch)

                # The one player name
                player = players.pop()

        except BufferError:
            return -1  # invalid name
        new_id = int(player.playerId)
        player_ids[original_name] = new_id  # store the new id in the dictionary

        # need to update the file now
        print("Added a new player the dictionary: " + player_name)
        with open("player_ids", 'w') as json_f:
            json.dump(player_ids, json_f)
        return new_id


print(get_player_id("AndrewChicken"))
print(get_player_id("\"GUNZJESTER PS4\""))
print(get_player_id("\"Tadd Nasty xbox\""))


# paladins_data = paladinsAPI.getMatchHistory(7241948)
# print(paladins_data)
