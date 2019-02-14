from discord import Game
from discord.ext import commands
from discord.ext.commands import Bot

import time

import PythonFunctions as Pf


# Discord Variables
BOT_PREFIX = ("!!", ">>")
BOT_STATUS = "!!help or >>help"

BOT_AUTHOR = "FeistyJalapeno#9045"
BOT_VERSION = "Version 2.0 Beta"
UPDATE_NOTES = "Added sub-command to stats command for elo stats."
ABOUT_BOT = "This bot was created since when Paladins selects random champions its not random. Some people are highly "\
            "likely to get certain roles and if you have a full team not picking champions sometime the game fails to "\
            "fill the last person causing the match to fail to start and kick everyone. This could be due to the game" \
            "trying to select a champion that has already been selected."


file_name = "token"
# Gets token from a file
with open(file_name, 'r') as f:
    TOKEN = f.readline().strip()
f.close()

# Creating client for bot
client = Bot(command_prefix=BOT_PREFIX)


# Get the some stats for a player while they are in a match.
@client.command(name='current',
                description="Get stats for people in a current match.",
                brief="Get stats for people in a current match.",
                pass_context=True,
                aliases=['cur', 'c'])
async def current(ctx, player_name):
    # await client.send_typing(ctx.channel)
    await client.say("```" + Pf.get_player_in_match(player_name) + "```")


# Calls different random functions based on input
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
    command = str(command).lower()
    if command == "damage":
        await client.say("Your random Damage champion is: " + "```css\n" + Pf.pick_damage() + "\n```")
    elif command == "flank":
        await client.say("Your random Flank champion is: " + "```" + Pf.pick_flank() + "```")
    elif command == "healer":
        await client.say("Your random Support/Healer champion is: " + "```" + Pf.pick_support() + "```")
    elif command == "tank":
        await client.say("Your random FrontLine/Tank champion is: " + "```" + Pf.pick_tank() + "```")
    elif command == "champ":
        await client.say("Your random champion is: " + "```" + Pf.pick_random_champ() + "```")
    elif command == "team":
        await  client.say("Your random team is: " + "```" + Pf.gen_team() + "```")
    elif command == "map" or command == "stage":
        await  client.say("Your random map is: " + "```" + Pf.pick_map() + "```")
    else:
        await client.say("Invalid command. For the random command please choose from one following options: "
                         "damage, flank, healer, tank, champ, team, or map. "
                         "\n For example: ```>>random damage``` will pick a random damage champion")


# Says a little more about the bot to discord users
@client.command(name='about',
                description="Learn more about the bot.",
                brief="Learn more about the bot.",
                aliases=['info', 'update'])
async def about():
    await client.say("Bot Author: " + BOT_AUTHOR + "\n"
                     "Bot Version: " + BOT_VERSION + "\n"
                     "Updated Notes: " + UPDATE_NOTES + "\n\n"
                     "About: " + ABOUT_BOT)


# Uses Paladins API to return detailed stats on a player
@client.command(name='stats',
                description="Returns simple stats of a champ for a player. \n"
                "stats <player_name> <champ> is the format of this command \n"
                "stats <player_name> Strix: \n will return the players stats on Strix. \n"
                "stats <player_name> me: \n will return the players overall stats."
                "stats <player_name> elo: \n will return the players elo stats.",
                brief="Returns simple stats of a champ for a player.",
                aliases=['stat'])
async def stats(player_name, champ="me"):
    await client.say("```" + Pf.get_champ_stats(player_name, champ) + "```")


# Handles errors when a user messes up the spelling or forgets an argument to a command
@client.event
async def on_command_error(error, ctx):
    channel = ctx.message.channel
    if isinstance(error, commands.MissingRequiredArgument):
        await client.send_message(channel, "A required argument to the command you called is missing"+"\N{CROSS MARK}")
    if isinstance(error, commands.BadArgument):  # This should do nothing since I check in functions for input error
        await client.send_message(channel, "Now you done messed up son.")
    elif isinstance(error, commands.CommandNotFound):
        await client.send_message(channel, f"\N{WARNING SIGN} {error}")


# We can use this code to track when people message this bot (a.k.a asking it commands)
@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    # Seeing if someone is using the bot_prefix and calling a command
    if message.content.startswith(BOT_PREFIX):
        print(message.author, message.content, message.channel, message.server)
    # Seeing if someone is using the bot_prefix and calling a command
    if message.content.startswith(">> ") or message.content.startswith("!! "):
        msg = 'Opps looks like you have a space after the bot prefix {0.author.mention}'.format(message)
        await client.send_message(message.channel, msg)
    """
    if message.content.startswith('*hello'):
        msg = 'Hello {0.author.mention}'.format(message)
        await client.send_message(message.channel, msg)
    elif message.content.startswith('*team'):
        await client.send_message(message.channel, str(gen_team()))
    """

    # Magical command...because on_message has priority over function commands
    await client.process_commands(message)


# Launching the bot function
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
# Starts the bot (its online)
client.run(TOKEN)

# client.close()
