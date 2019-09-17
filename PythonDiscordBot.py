import discord
from discord.ext import commands
from discord.ext.commands import Bot

import asyncio
import aiohttp.client_exceptions as aiohttp_client_exceptions
import concurrent.futures
import random
import json
import traceback
from socket import gaierror
import requests
import os

import my_utils as helper
from cogs import PaladinsAPI

from colorama import Fore, init
init(autoreset=True)


# Discord Variables
BOT_STATUS = ">>help"

BOT_AUTHOR = "FeistyJalapeno#9045"
BOT_VERSION = "Version 4.3.1 Beta"
GAME = ["Paladins", BOT_STATUS, BOT_VERSION, BOT_STATUS, "Features"]

file_name = "token"
# Gets token and prefix from a file
with open(file_name, 'r') as f:
    TOKEN = f.readline().strip()
    PREFIX = f.readline().strip()
f.close()


def get_prefix(bot, message):
    default_prefix = [PREFIX]
    # print("killing your hard drive")
    if message.guild:
        try:
            with open("languages/server_configs") as json_f:
                server_conf = json.load(json_f)
                try:
                    default_prefix = server_conf[str(message.guild.id)]["prefix"].split(",")
                except KeyError:
                    pass
        except FileNotFoundError:
            pass
    return commands.when_mentioned_or(*default_prefix)(bot, message)


# Creating client for bot
client = Bot(command_prefix=get_prefix)
client.remove_command('help')  # Removing default help command.


# Bot tries to message the error in the channel where its caused and then tries to dm the error to the user
@client.event
async def send_error(cont, msg):
    error_msg = "```diff\n- {}```".format(msg)
    try:  # First lets try to send the message to the channel the command was called
        await cont.send(error_msg)
        print(Fore.RED + str(msg))
    except BaseException as e:
        print(e)
        try:  # Next lets try to DM the message to the user
            author = cont.message.author
            await author.send(error_msg)
            print(Fore.RED + str(msg))
        except BaseException:  # Bad sign if we end up here but is possible if the user blocks some DM's
            print("The bot can't message the user in their DM's or in the channel they called the function.")


# Handles errors when a user messes up the spelling or forgets an argument to a command or an error occurs
# """
@client.event
async def on_command_error(ctx, error):
    # checks for non-discord command related errors
    if hasattr(error, "original"):
        # Catches connection related exceptions
        # """
        if isinstance(error.original, aiohttp_client_exceptions.ClientError) or isinstance(error.original, gaierror) or\
                isinstance(error.original, ConnectionError) or isinstance(error.original, TimeoutError) or \
                isinstance(error.original, requests.exceptions.RequestException) or \
                isinstance(error.original, concurrent.futures.TimeoutError):
            await send_error(cont=ctx, msg="Connection error. Please try again.")
            return None
        # """
        if isinstance(error.original, discord.Forbidden):
            await send_error(cont=ctx, msg="The bot does not have permission to send messages in the channel:\n{}"
                                           "\n\n- where "
                                           "you just called the command:\n{}".format(ctx.channel, ctx.message.content))
            return None
        elif isinstance(error.original, MemoryError):
            await send_error(cont=ctx, msg="Your lucky... you caused the bot to run out of memory. Don't worry though"
                                           "... the bot will recover. Please try again.")

        # Checking different types of ValueError (only closed file for now)
        elif isinstance(error.original, ValueError):
            if str(error.original) == "I/O operation on closed file.":
                await send_error(cont=ctx, msg="The bot tried to send you a file/image but it has been taken away from"
                                               "the bot...probably because of an internet fluke. Please try again.")
                return None

    # Checks for discord command errors
    if isinstance(error, commands.MissingRequiredArgument):
        await send_error(cont=ctx, msg="A required argument to the command you called is missing.")
    elif isinstance(error, commands.BadArgument):
        await send_error(cont=ctx, msg="Make sure the command is in the correct format.")
    elif isinstance(error, commands.errors.UnexpectedQuoteError):
        await send_error(cont=ctx, msg="If you are trying to type the name Mal`Damba please type his name as one "
                                       "word without any kinda of quote marks.")
    elif isinstance(error, commands.errors.ExpectedClosingQuoteError):
        await send_error(cont=ctx, msg="You forgot a Quote(\") when typing a player name.")
    elif isinstance(error, commands.TooManyArguments):
        await send_error(cont=ctx, msg=error)
    elif isinstance(error, commands.CommandNotFound):
        msg = f"\N{WARNING SIGN} {error}"
        await send_error(cont=ctx, msg=msg)
    elif isinstance(error, commands.CommandOnCooldown):
        await send_error(cont=ctx, msg=error)
    elif isinstance(error, commands.MissingPermissions):
        await send_error(cont=ctx, msg=error)
    elif isinstance(error, commands.NotOwner):
        await send_error(cont=ctx, msg=error)
    elif isinstance(error, commands.CheckFailure):
        await send_error(cont=ctx, msg=error)
    else:
        global daily_error_count
        daily_error_count = daily_error_count + 1
        print(Fore.RED + "An uncaught error occurred: ", error)  # More error checking
        error_file = str(await helper.get_est_time()).replace("/", "-").replace(":", "-").split()
        error_file = "_".join(error_file[::-1])
        with open("error_logs/{}.csv".format(error_file), 'w+', encoding="utf-8") as error_log_file:
            error_trace = str(ctx.message.content) + "\n\n"
            error_log_file.write(error_trace)
            traceback.print_exception(type(error), error, error.__traceback__, file=error_log_file)

        msg = "Unfortunately, something really messed up. If you entered the command correctly just wait a few seconds"\
              " and then try again. If the problem occurs again it is most likely a bug that will need be fixed."
        await send_error(cont=ctx, msg=msg)
# """


# We can use this code to track when people message this bot (a.k.a asking it commands)
@client.event
async def on_message(message):
    channel = message.channel
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    # Seeing if someone is using the bot_prefix and calling a command
    if message.content.startswith(PREFIX):
        print(message.author, message.content, channel, message.guild, await helper.get_est_time())
        global daily_command_count
        daily_command_count = daily_command_count + 1
    # Seeing if someone is using the bot_prefix and calling a command
    if message.content.startswith(PREFIX + " "):
        msg = 'Oops looks like you have a space after the bot prefix {0.author.mention}'.format(message)
        try:  # First lets try to send the message to the channel the command was called
            await message.channel.send(msg)
        except BaseException:
            try:    # Next lets try to DM the message to the user
                await message.author.send(msg)
            except BaseException:  # Bad sign if we end up here but is possible if the user blocks some DM's
                print("The bot can't message the user in their DM's or in the channel they called the function.")

    # on_message has priority over function commands
    await client.process_commands(message)


# Resets command uses for -a on the current command at 6am everyday
@client.event
async def reset_uses():
    await client.wait_until_ready()
    sleep_time = await helper.get_seconds_until_reset()
    await asyncio.sleep(sleep_time)
    while not client.is_closed():
        await helper.reset_command_uses()
        updater = PaladinsAPI.PaladinsAPICog(client)
        for discord_id in os.listdir("user_data"):
            await updater.auto_update(discord_id)
        await asyncio.sleep(60*60*24)  # day


# Logs to a file server count, errors, commands used, api calls used (every hour to get a daily stats)
@client.event
async def log_information():
    await client.wait_until_ready()
    sleep_time = await helper.get_second_until_hour()
    await asyncio.sleep(sleep_time)
    while not client.is_closed():
        with open("log_file.csv", 'r') as r_log_file:
            global daily_command_count
            global daily_error_count
            date = await helper.get_est_time()
            date = date.split(" ")[1]

            lines = r_log_file.read().splitlines()
            servers, n1, old_errors, num_cmd, old_api_calls, old_date = lines[-1].split(',')
            api_calls = PaladinsAPI.paladinsAPI.getDataUsed()
            api_calls = api_calls.totalRequestsToday

            ss_c = str(len(client.get_guild(554372822739189761).members))

            # Updates tracked information for the current day or the next day
            if old_date.strip() == date:
                lines[-1] = "{}, {}, {}, {}, {}, {}\n".format(len(client.guilds), ss_c, int(daily_error_count) +
                                                              int(old_errors), int(daily_command_count) + int(num_cmd),
                                                              api_calls, date)
                with open("log_file.csv", 'w') as w_log_file:
                    w_log_file.write("\n".join(lines))
            else:
                with open("log_file.csv", '+a') as a_log_file:
                    a_log_file.write("{}, {}, {}, {}, {}, {}\n".format(len(client.guilds), ss_c, int(daily_error_count),
                                                                       daily_command_count, api_calls, date))
        daily_command_count = 0
        daily_error_count = 0
        print("Logged commands and server count: {}".format(await helper.get_est_time()))
        await asyncio.sleep(60*60)  # Log information every hour


# Launching the bot function
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print('------')
    global daily_command_count
    daily_command_count = 0
    global daily_error_count
    daily_error_count = 0
    client.loop.create_task(reset_uses())
    client.loop.create_task(change_bot_presence())
    if PREFIX != '&&':  # Prevents test bot from messing up bot stats log
        client.loop.create_task(log_information())
    await count_servers()
    print("Client is fully online and ready to go...")


# Prints the number of servers the bot is in
@client.event
async def count_servers():
    await client.wait_until_ready()
    if not client.is_closed():
        print(Fore.GREEN + "Current servers:", Fore.MAGENTA + str(len(client.guilds)))
        print(Fore.GREEN + "Members in support server:", Fore.MAGENTA +
              str(len(client.get_guild(554372822739189761).members)))


# Changes bot presence every min
@client.event
async def change_bot_presence():
    secure_random = random.SystemRandom()
    while 1:
        # This will throw a connection error once the bot goes offline but nothing seems to prevent this so a try
        # except code block must be used to prevent an error from being thrown
        try:
            await client.change_presence(status=discord.Status.dnd,  # Online, idle, invisible, dnd
                                         activity=discord.Game(name=secure_random.choice(GAME), type=0))
        except BaseException:
            pass
        await asyncio.sleep(60)  # Ever min


# Below cogs represents the folder our cogs are in. The dot is like an import path.
initial_extensions = ['cogs.help', 'cogs.rand', 'cogs.PaladinsAPI', 'cogs.solo_commands']
# initial_extensions = ['cogs.help', 'cogs.rand', 'cogs.PaladinsAPI', 'cogs.solo_commands', 'cogs.new_api']


# Here we load our extensions(cogs) listed above in [initial_extensions].
def load_cogs():
    for extension in initial_extensions:
        try:
            client.load_extension(extension)
            print(Fore.GREEN + "Loaded extension:", Fore.MAGENTA + extension)
        except BaseException as e:
            print(Fore.RED + "Failed to load: {} because of {}".format(extension, e))
    print("")


load_cogs()

# Start the bot
client.run(TOKEN, bot=True, reconnect=True)
