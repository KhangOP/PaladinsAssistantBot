import discord
from discord.ext import commands
from discord.ext.commands import Bot

import asyncio
import random
import json

import my_utils as helper
from cogs import PaladinsAPI


# Discord Variables
BOT_STATUS = ">>help"

BOT_AUTHOR = "FeistyJalapeno#9045"
BOT_VERSION = "Version 4.1.1 Beta"
UPDATE_NOTES = "Changed 3 functions to be embeds to include images."
GAME = ["Paladins", BOT_STATUS, BOT_VERSION, BOT_STATUS, "Errors"]

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
    try:  # First lets try to send the message to the channel the command was called
        await cont.send(msg)
    except BaseException:
        try:  # Next lets try to DM the message to the user
            # await client.send_message(cont.message.author, msg)
            await cont.send(msg)
        except BaseException:  # Bad sign if we end up here but is possible if the user blocks some DM's
            print("The bot can't message the user in their DM's or in the channel they called the function.")


# Handles errors when a user messes up the spelling or forgets an argument to a command or an error occurs
# """
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await send_error(cont=ctx, msg="A required argument to the command you called is missing"+"\N{CROSS MARK}")
    elif isinstance(error, commands.BadArgument):  # This should do nothing since I check in functions for input error
        await send_error(cont=ctx, msg="Make sure the command is in the correct format.")
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
        print("An uncaught error occurred: ", error)  # More error checking
        msg = "Unfortunately, something messed up. If you entered the command correctly just wait a few seconds " \
              "and then try again. \n\n \N{CROSS MARK}"
        # " Please dm me the error or post this error in the error channel" \
        # "of the bot support server if the problem keeps happening:\n\n`" + str(error) + "`"
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
                await message.channel.send(msg)
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
        await asyncio.sleep(60*60*24)  # day


# Logs to a file server count, errors, commands used, api calls used (every hour to get a daily stats)
@client.event
async def log_information():
    await client.wait_until_ready()
    sleep_time = await helper.get_seconds_until_reset()
    await asyncio.sleep(sleep_time)
    while not client.is_closed():
        with open("log_file.csv", 'r') as r_log_file:
            global daily_command_count
            global daily_error_count
            date = await helper.get_est_time()
            date = date.split(" ")[1]

            lines = r_log_file.read().splitlines()
            servers, old_errors, num_cmd, old_api_calls, old_date = lines[-1].split(',')
            api_calls = PaladinsAPI.paladinsAPI.getDataUsed()
            api_calls = api_calls.totalRequestsToday

            # if this is less than that means that the api calls have been reset
            if api_calls < int(old_api_calls):
                api_calls = old_api_calls

            # Updates tracked information for the current day or the next day
            if old_date.strip() == date:
                lines[-1] = "{}, {}, {}, {}, {}".format(len(client.guilds), int(daily_error_count) + int(old_errors),
                                                        int(daily_command_count) + int(num_cmd), str(api_calls),
                                                        date)
                with open("log_file.csv", 'w') as w_log_file:
                    w_log_file.write("\n".join(lines))
            else:
                with open("log_file.csv", '+a') as a_log_file:
                    a_log_file.write("{}, {}, {}, {}, {}\n".format(str(len(client.guilds)), str(int(daily_error_count)),
                                                                   str(daily_command_count), api_calls, date))
        daily_command_count = 0
        daily_error_count = 0
        print("Logged commands and server count.")
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
    client.loop.create_task(log_information())
    await count_servers()
    print("Client is fully online and ready to go...")


# Prints the number of servers the bot is in
@client.event
async def count_servers():
    await client.wait_until_ready()
    if not client.is_closed():
        print("Current servers:", len(client.guilds))


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


# Here we load our extensions(cogs) listed above in [initial_extensions].
def load_cogs():
    for extension in initial_extensions:
        try:
            client.load_extension(extension)
            print("loaded extension:", extension)
        except helper.MyException:
            print("failed to load: ", extension)


load_cogs()

# Start the bot
client.run(TOKEN, bot=True, reconnect=True)
