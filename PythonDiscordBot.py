import discord
from discord.ext import commands
from discord.ext.commands import Bot

import asyncio
import random

import my_utils as helper

# Discord Variables
BOT_PREFIX = ("!!", ">>")
BOT_STATUS = "!!help or >>help"

BOT_AUTHOR = "FeistyJalapeno#9045"
BOT_VERSION = "Version 4.0.1 Beta"
UPDATE_NOTES = "Changed 3 functions to be embeds to include images."
GAME = ["Paladins", BOT_STATUS, BOT_VERSION, BOT_STATUS, "Errors"]


file_name = "token"
# Gets token from a file
with open(file_name, 'r') as f:
    TOKEN = f.readline().strip()
f.close()

# Creating client for bot
client = Bot(command_prefix=BOT_PREFIX)
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
        return 0
    if isinstance(error, commands.BadArgument):  # This should do nothing since I check in functions for input error
        await send_error(cont=ctx, msg="Make sure the command is in the correct format.")
    elif isinstance(error, commands.CommandNotFound):
        msg = f"\N{WARNING SIGN} {error}"
        await send_error(cont=ctx, msg=msg)
    elif isinstance(error, commands.CommandOnCooldown):
        await send_error(cont=ctx, msg=error)
    else:
        print("An uncaught error occurred: ", error)  # More error checking
        msg = "Unfortunately, something messed up. If you entered the command correctly just wait a few seconds " \
              "and then try again."
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
    if message.content.startswith(BOT_PREFIX):
        print(message.author, message.content, channel, message.guild, await helper.get_est_time())
    # Seeing if someone is using the bot_prefix and calling a command
    if message.content.startswith(">> ") or message.content.startswith("!! "):
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


# Launching the bot function
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print('------')
    await count_servers()
    await change_bot_presence()
    print("Client is fully online and ready to go...")


# Prints the number of servers the bot is in
@client.event
async def count_servers():
    await client.wait_until_ready()
    if not client.is_closed():
        print("Current servers:", len(client.guilds))


# Changes bot presence every min
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
initial_extensions = ['cogs.help', 'cogs.rand', 'cogs.PaladinsAPI']


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
