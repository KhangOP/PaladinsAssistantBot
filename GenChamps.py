import random
import traceback
import asyncio
import requests
from bs4 import BeautifulSoup

from discord import Game
from discord.ext import commands
from discord.ext.commands import Bot

# Discord Variables
BOT_PREFIX = ("!!", ">>")
BOT_STATUS = "!!help or >>help"

BOT_AUTHOR = "FeistyJalapeno#9045"
BOT_VERSION = "Version 1.6.4"
UPDATE_NOTES = "Added sub-command to stats command for elo stats."
ABOUT_BOT = "This bot was created since when Paladins selects random champions its not random. Some people are highly "\
            "likely to get certain roles and if you have a full team not picking champions sometime the game fails to "\
            "fill the last person causing the match to fail to start and kick everyone. This could be due to the game" \
            "trying to select a champ that has already been selected."

file_name = "token"
# Gets token from a file
with open(file_name, 'r') as f:
    TOKEN = f.read().replace('\n', '')
f.close()

client = Bot(command_prefix=BOT_PREFIX)


# List of Champs by Class
DAMAGES = ["Cassie", "Kinessa", "Drogoz", "Bomb King", "Viktor", "Sha Lin", "Tyra", "Willo", "Lian", "Strix", "Vivian",
          "Dredge", "Imani"]
FLANKS = ["Skye", "Buck", "Evie", "Androxus", "Meave", "Lex", "Zhin", "Talus", "Moji", "Koga"]
FRONTLINES = ["Barik", "Fernando", "Ruckus", "Makoa", "Torvald", "Inara", "Ash", "Terminus", "Khan"]
SUPPORTS = ["Grohk", "Grover", "Ying", "Mal'Damba", "Seris", "Jenos", "Furia"]

# Map Names
MAPS = ["Frog Isle", "Jaguar Falls", "Serpent Beach", "Frozen Guard", "Ice Mines", "Ice Mines", "Fish Market",
        "Timber Mill", "Stone Keep", "Brightmarsh", "Splitstone Quarry", "Ascension Peak", "Warder's Gate"]


# Prints when a function has been called
def log_function_call():
    print("Function called")


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
    team = []
    team.append(pick_damage())
    team.append(pick_flank())
    team.append(pick_support())
    team.append(pick_tank())

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


def get_champ_stats(player_name, champ):
    player_name = str(player_name)
    champ = str(champ).lower().capitalize()

    # Personal stats
    if champ == "Me":
        return get_global_stats(player_name)

    # Personal stats
    if champ == "Elo":
        return get_player_elo(player_name)

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
    yes = 0

    info = []
    matches = 0

    # Gathering the info we want
    for i, row in enumerate(data):
        data[i] = data[i].replace("/", "").strip()
        if data[i] == champ and data[i - 1] != "Refresh Data":  # (if player name = champ name they are looking for)
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


"""End of Python Functions"""


# Calls python functions
@client.command(name='random',
                description="Picks a random champ(s) based on the given input. \n"
                            "damage - Picks a random Damage champion. \n"
                            "healer - Picks a random Support/Healer champion. \n"
                            "flank -  Picks a random Flank champion. \n"
                            "tank -   Picks a random FrontLine/Tank champion. \n"
                            "champ -  Picks a random champion from any class. \n"
                            "team -   Picks a random team. "
                            "It will always pick (1 Damage, 1 Flank, 1 Support, and 1 FrontLine, "
                            "and then one other champion.) \n"
                            "map - Picks a random siege/ranked map.",
                brief="Picks a random champ(s) based on the given input.",
                aliases=['rand', 'r'])
async def rand(command):
    log_function_call()
    command = str(command).lower()
    if command == "damage":
        await client.say("Your random Damage champion is: " + "```" + pick_damage() + "```")
    elif command == "flank":
        await client.say("Your random Flank champion is: " + "```" + pick_flank() + "```")
    elif command == "healer":
        await client.say("Your random Support/Healer champion is: " + "```" + pick_support() + "```")
    elif command == "tank":
        await client.say("Your random FrontLine/Tank champion is: " + "```" + pick_tank() + "```")
    elif command == "champ":
        await client.say("Your random champion is: " + "```" + pick_random_champ() + "```")
    elif command == "team":
        await  client.say("Your random team is: " + "```" + gen_team() + "```")
    elif command == "map" or command == "stage":
        await  client.say("Your random map is: " + "```" + pick_map() + "```")
    else:
        await client.say("Invalid command. For the random command please choose from one following options: "
                         "damage, flank, healer, tank, champ, team, or map. "
                         "\n For example: ```>>random damage``` will pick a random damage champion")


@client.command(name='about',
                description="Learn more about the bot.",
                brief="Learn more about the bot.",
                aliases=['info', 'update'])
async def about():
    log_function_call()
    await client.say("Bot Author: " + BOT_AUTHOR + "\n"
                     "Bot Version: " + BOT_VERSION + "\n"
                     "Updated Notes: " + UPDATE_NOTES + "\n\n"
                     "About: " + ABOUT_BOT)


@client.command(name='stats',
                description="Returns simple stats of a champ for a player. \n"
                "stats <player_name> <champ> is the format of this command \n"
                "stats <player_name> Strix: \n will return the players stats on Strix. \n"
                "stats <player_name> me: \n will return the players overall stats."
                "stats <player_name> elo: \n will return the players elo stats.",
                brief="Returns simple stats of a champ for a player.",
                aliases=['stat'])
async def stats(player_name, champ):
    log_function_call()
    await client.say("```" + get_champ_stats(player_name, champ) + "```")


# Handles errors when a user messes up the spelling or forgets an argument to a command
@client.event
async def on_command_error(error, ctx):
    channel = ctx.message.channel
    if isinstance(error, commands.MissingRequiredArgument):
        await client.send_message(channel, "A required argument to the command you called is missing"+"\N{CROSS MARK}")
    elif isinstance(error, commands.BadArgument):  # This should do nothing since I check in functions for input error
        await client.send_message(channel, "Now you done messed up son.")
    elif isinstance(error, commands.CommandNotFound):
        await client.send_message(channel, f"\N{WARNING SIGN} {error}")


# This code for some reason does not work other discord functions and cause the bot to only respond to these commands
"""
@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    if message.content.startswith('*hello'):
        msg = 'Hello {0.author.mention}'.format(message)
        await client.send_message(message.channel, msg)
    elif message.content.startswith('*team'):
        await client.send_message(message.channel, str(gen_team()))
"""


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    # Status of the bot
    await client.change_presence(game=Game(name=BOT_STATUS))


"""
async def list_servers():
    await client.wait_until_ready()
    while not client.is_closed:
        print("Current servers: ")
        for server in client.servers:
            print(server.name)
        await asyncio.sleep(600)
"""

"""
@client.command()
async def stats():
    url = "http://paladins.guru/profile/pc/FeistyJalapeno"
    response = requests.get(url)
    value = response.json()
    print(value)
    await client.say(value)
"""

# client.loop.create_task(list_servers())

# Must be called after Discord functions
client.run(TOKEN)

"""Main Function"""
"""
def main():
    gen_team()
    print(pick_random_champ())


main()
"""
