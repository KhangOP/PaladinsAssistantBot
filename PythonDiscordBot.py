import discord
from discord import Game
from discord.ext import commands
from discord.ext.commands import Bot

from concurrent.futures import ThreadPoolExecutor

import time
import asyncio
import random

import PythonFunctions as Pf


# Discord Variables
BOT_PREFIX = ("!!", ">>")
BOT_STATUS = "!!help or >>help"

BOT_AUTHOR = "FeistyJalapeno#9045"
BOT_VERSION = "Version 3.0.0 Beta"
UPDATE_NOTES = "Added executor to prevent blocking which causes delays or crashes the bot when returning the results"
ABOUT_BOT = "This bot was created since when Paladins selects random champions its not random. Some people are highly "\
            "likely to get certain roles and if you have a full team not picking champions sometime the game fails to "\
            "fill the last person causing the match to fail to start and kick everyone. This could be due to the game" \
            "trying to select a champion that has already been selected."
GAME = ["Paladins", BOT_STATUS, BOT_VERSION, BOT_STATUS, "Errors"]


file_name = "token"
# Gets token from a file
with open(file_name, 'r') as f:
    TOKEN = f.readline().strip()
f.close()

# Creating client for bot
client = Bot(command_prefix=BOT_PREFIX)
client.remove_command('help')  # Removing default help command.


# Get the some stats for a player while they are in a match.
@client.command(name='history',
                description="Get simple stats for a player's last amount of matches.",
                brief="Get simple stats for a player's last amount of matches.",
                pass_context=True)
async def history(ctx, player_name, amount=10):
    await client.send_typing(ctx.message.channel)  # It works... pretty cool
    # Prevents blocking so that function calls are not delayed
    executor = ThreadPoolExecutor(max_workers=1)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, Pf.get_history, player_name, amount)
    await client.say("```diff\n" + result + "```")
    # await client.say("```diff\n" + Pf.get_history(player_name, amount) + "```")


# Get the some stats for a player while they are in a match.
@client.command(name='last',
                description="Get stats for a player in their last match.",
                brief="Get stats for a player in their last match.")
async def last(player_name):
    # Prevents blocking so that function calls are not delayed
    executor = ThreadPoolExecutor(max_workers=1)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, Pf.get_history_simple, player_name)
    await client.say("```" + result + "```")
    # await client.say("```" + Pf.get_history_simple(player_name) + "```")


# Get the some stats for a player while they are in a match.
@client.command(name='current',
                description="Get stats for a player's current match.",
                brief="Get stats for a player's current match.",
                pass_context=True,
                aliases=['cur', 'c'])
async def current(ctx, player_name):
    await client.send_typing(ctx.message.channel)  # It works... pretty cool
    # Prevents blocking so that function calls are not delayed
    executor = ThreadPoolExecutor(max_workers=1)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, Pf.get_player_in_match, player_name)
    await client.say("```diff\n" + result + "```")


# Calls different random functions based on input
@client.command(name='random',
                description="Picks a random (champ, team, or map) based on the given input command which can be: \n\n"
                            "damage - Picks a random Damage champion. \n"
                            "healer - Picks a random Support/Healer champion. \n"
                            "flank  - Picks a random Flank champion. \n"
                            "tank   - Picks a random FrontLine/Tank champion. \n"
                            "champ  - Picks a random champion from any class. \n"
                            "team   - Picks a random team. "
                            "It will always pick (1 Damage, 1 Flank, 1 Support, and 1 FrontLine, "
                            "and then one other champion.) \n"
                            "map    - Picks a random siege/ranked map.",
                brief="Picks a random (champ, team, or map) based on the given input command.",
                aliases=['rand', 'r'])
async def rand(command):
    command = str(command).lower()
    if command == "damage":
        await client.say("Your random Damage champion is: " + "```css\n" + Pf.pick_damage() + "```")
    elif command == "flank":
        await client.say("Your random Flank champion is: " + "```css\n" + Pf.pick_flank() + "```")
    elif command == "healer":
        await client.say("Your random Support/Healer champion is: " + "```css\n" + Pf.pick_support() + "```")
    elif command == "tank":
        await client.say("Your random FrontLine/Tank champion is: " + "```css\n" + Pf.pick_tank() + "```")
    elif command == "champ":
        await client.say("Your random champion is: " + "```css\n" + Pf.pick_random_champ() + "```")
    elif command == "team":
        await  client.say("Your random team is: " + "```css\n" + Pf.gen_team() + "```")
    elif command == "map" or command == "stage":
        await  client.say("Your random map is: " + "```css\n" + Pf.pick_map() + "```")
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
                description="Returns simple stats based on the option they choose: \n\n"
                ">>stats <player_name> Strix: \nwill return the player's stats on Strix. \n\n"
                ">>stats <player_name> me: \nwill return the player's overall stats. \n\n"
                ">>stats <player_name> elo: \nwill return the player's Guru elo.",
                brief="Returns simple stats for a player.",
                aliases=['stat'])
async def stats(player_name, option="me", space=""):
    if space != "":
        option += " " + space
    # Prevents blocking so that function calls are not delayed
    executor = ThreadPoolExecutor(max_workers=1)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, Pf.get_champ_stats, player_name, option)
    await client.say("```" + result + "```")
    # await client.say("```" + Pf.get_champ_stats(player_name, champ) + "```")


# Handles errors when a user messes up the spelling or forgets an argument to a command
@client.event
async def on_command_error(error, ctx):
    channel = ctx.message.channel
    if isinstance(error, commands.MissingRequiredArgument):
        await client.send_message(channel, "A required argument to the command you called is missing"+"\N{CROSS MARK}")
        return -1
    if isinstance(error, commands.BadArgument):  # This should do nothing since I check in functions for input error
        await client.send_message(channel, "Now you done messed up son.")
        return -1
    elif isinstance(error, commands.CommandNotFound):
        await client.send_message(channel, f"\N{WARNING SIGN} {error}")
        return -1
    else:
        print("An uncaught error occurred: ", error)  # More error checking
        return -1


# We can use this code to track when people message this bot (a.k.a asking it commands)
@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    # Seeing if someone is using the bot_prefix and calling a command
    if message.content.startswith(BOT_PREFIX):
        print(message.author, message.content, message.channel, message.server, Pf.get_est_time())
        # if str(message.author) == "FeistyJalapeno#9045":  # This works ^_^
        #    print("Hello creator.")
    # Seeing if someone is using the bot_prefix and calling a command
    if message.content.startswith(">> ") or message.content.startswith("!! "):
        msg = 'Opps looks like you have a space after the bot prefix {0.author.mention}'.format(message)
        try:
            await client.send_message(message.author, msg)
        except:
            print("Bot does not have permission to print to this channel")  # Temp fix
        # await client.send_message(message.channel, msg)
    """
    if message.content.startswith('*hello'):
        msg = 'Hello {0.author.mention}'.format(message)
        await client.send_message(message.channel, msg)
    elif message.content.startswith('*team'):
        await client.send_message(message.channel, str(gen_team()))
    """

    # Magical command...because on_message has priority over function commands
    await client.process_commands(message)


# Custom help commands
@client.group(pass_context=True)
async def help(ctx):
    await client.say("Help commands are currently being reworked. If you have a question just dm FeistyJalapeno#9045")

    if ctx.invoked_subcommand is None:
        author = ctx.message.author
        embed = discord.Embed(
            colour=discord.colour.Color.dark_teal()
        )
        embed.set_author(name='PaladinsAssistant Commands: ')
        embed.set_thumbnail(url="https://mypaladins.com/images/paladins/champions/2417.jpg?v=nBF1oAzzG0m0XfoBSuWFwlHsLkORCTHVLyLdqDK1C9A")
        embed.set_image(url="https://mypaladins.com/images/paladins/champions/2417.jpg?v=nBF1oAzzG0m0XfoBSuWFwlHsLkORCTHVLyLdqDK1C9A")
        embed.set_footer(icon_url="https://cdn.discordapp.com/embed/avatars/0.png",
                         text="Bot created by FeistyJalapeno#9045. If you have questions, suggestions, "
                              "found a bug, etc. feel free to DM me.")
        embed.add_field(name='help', value='Returns this message.', inline=False)
        embed.add_field(name='about', value='Returns more information about the bot.', inline=False)
        embed.add_field(name='last', value='Returns stats for a player\'s last match.', inline=False)
        embed.add_field(name='stats', value='Returns simple overall stats for a player.', inline=False)
        embed.add_field(name='random', value='Randomly chooses a map, champion, or team to help with custom matches.',
                        inline=False)
        embed.add_field(name='current', value='Returns stats for a player\'s current match.', inline=False)
        embed.add_field(name='history', value='Returns simple stats for a player\'s last amount of matches.',
                        inline=False)

        # Parameters: `player_name`

        await client.send_message(author, embed=embed)


@help.command()
async def about():
    await client.say("```Returns more information about the bot.```")


@help.command(pass_context=True)
async def last(ctx):
    """
    message = str("```{}\n\n{}\n{}```").format("Returns stats for a player\'s last match.",
                                               "Command format:",
                                               ">>random <player_name>")
    """
    '''
    author = ctx.message.author
    embed = discord.Embed(
        colour=discord.colour.Color.dark_teal()
    )
    # embed.set_author(name='>>Last Returns stats for a player\'s last match.')
    # embed.set_footer(icon_url="https://cdn.discordapp.com/embed/avatars/0.png",
    #                 text="Bot created by FeistyJalapeno#9045. If you have questions, suggestions, "
    #                      "found a bug, etc. feel free to DM me.")
    """
    embed.add_field(name='Command Name:', value='```fix\nlast```', inline=False)
    embed.add_field(name='Command Description:', value='```\nReturns stats for a player\'s last match.```', inline=False)
    embed.add_field(name='Command format:', value='```css\n>>last <player_name>```', inline=False)
    embed.add_field(name='Command format:', value='Random message that is not important.', inline=False)
    """

    embed.add_field(name='Command Name:', value='```md\nlast```', inline=False)
    embed.add_field(name='Description:', value='```fix\nReturns stats for a player\'s last match.```',
                    inline=False)
    embed.add_field(name='Format:', value='```md\n>>last <player_name>```', inline=False)
    embed.add_field(name='Parameters:', value='```md\n <player_name> Players Paladins IGN```', inline=False)
    
    await client.say(embed=embed)
    '''
    await client.say(embed=create_embed("last", "Returns stats for a player\'s last match.", "player_name",
                                        "Players Paladins IGN"))


def create_embed(name, info, pars, des):
    embed = discord.Embed(
        colour=discord.colour.Color.dark_teal()
    )

    embed.add_field(name='Command Name:', value='```md\n' + name + '```', inline=False)
    embed.add_field(name='Description:', value='```fix\n' + info + '```',
                    inline=False)
    # print(len(pars))
    embed.add_field(name='Format:', value='```md\n>>' + name + " <" + pars + '>```', inline=False)
    embed.add_field(name='Parameters:', value='```md\n<' + pars + "> " + des + '```', inline=False)

    return embed

# @help.command()
# async def last():
#    await client.say("Bot Author: " + BOT_AUTHOR + "\n" + "Bot Version: " + BOT_VERSION + "\n" + "Updated Notes: " +
#                     UPDATE_NOTES + "\n\n" + "About: " + ABOUT_BOT)


sleep_time = 5
backoff_multiplier = 1


# Launching the bot function
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    # print(client.user.id)
    print('------')
    # Status of the bot
    global backoff_multiplier
    backoff_multiplier = 1
    # Online, idle, invisible, dnd
    await client.change_presence(game=Game(name=BOT_STATUS, type=0), status='dnd')
    print("Client is fully online and ready to go...")

"""
async def list_servers():
    await client.wait_until_ready()
    while not client.is_closed:
        print("Current servers: ")
        for server in client.servers:
            print(server.name)
        await asyncio.sleep(600)
"""


# Testing bot presence changing
async def change_bot_presence():
    await client.wait_until_ready()
    secure_random = random.SystemRandom()
    while not client.is_closed:
        await client.change_presence(game=Game(name=secure_random.choice(GAME), type=0), status='dnd')
        await asyncio.sleep(60)  # Ever min


client.loop.create_task(change_bot_presence())

# Must be called after Discord functions
# Starts the bot (its online)

while True:
    try:
        client.loop.run_until_complete(client.start(TOKEN))
    except BaseException:  # Bad practice but is fine to use in this case
        print("Disconnected, going to try to reconnect in " + str(sleep_time*backoff_multiplier) + " seconds.")
        time.sleep(sleep_time*backoff_multiplier)
        backoff_multiplier += 1
