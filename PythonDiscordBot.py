import discord
from discord.ext import commands
from discord.ext.commands import Bot

from concurrent.futures import ThreadPoolExecutor

import asyncio
import random

import PythonFunctions as Pf
import MyException as MyException

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
    else:
        print("An uncaught error occurred: ", error)  # More error checking
        msg = "Welp, something messed up. If you entered the command correctly just wait a few seconds and then try " \
              "again."
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
        print(message.author, message.content, channel, message.guild, Pf.get_est_time())
        # if str(message.author) == "FeistyJalapeno#9045":  # This works ^_^
        #    print("Hello creator.")
    # Seeing if someone is using the bot_prefix and calling a command
    if message.content.startswith(">> ") or message.content.startswith("!! "):
        msg = 'Oops looks like you have a space after the bot prefix {0.author.mention}'.format(message)
        try:  # First lets try to send the message to the channel the command was called
            # await client.send_message(channel, msg)
            await message.channel.send(msg)
        except MyException:
            try:    # Next lets try to DM the message to the user
                # await client.send_message(message.author, msg)
                await message.channel.send(msg)
            except MyException:  # Bad sign if we end up here but is possible if the user blocks some DM's
                print("The bot can't message the user in their DM's or in the channel they called the function.")

    # on_message has priority over function commands
    await client.process_commands(message)

'''
@client.command(name='test',
                pass_context=True,
                aliases=['t'])
async def test(ctx):
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

sleep_time = 5
backoff_multiplier = 1


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


# Changing bot presence
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


# Below cogs represents the folder our cogs are in. Following is the file name. So 'meme.py' in cogs, would be cogs.meme
# Think of it like a dot path import
initial_extensions = ['cogs.help', 'cogs.rand', 'cogs.PaladinsAPI']


# Here we load our extensions(cogs) listed above in [initial_extensions].
def load_cogs():
    for extension in initial_extensions:
        try:
            client.load_extension(extension)
            print("loaded extension:", extension)
        except MyException:
            print("failed to load: ", extension)


load_cogs()

client.run(TOKEN, bot=True, reconnect=True)

# Loop that allows the bot to reconnect if the internet goes out
"""
while True:
    try:
        client.loop.run_until_complete(client.start(TOKEN))
    except BaseException:  # Bad practice but is fine to use in this case
        print("Disconnected, going to try to reconnect in " + str(sleep_time*backoff_multiplier) + " seconds.")
        time.sleep(sleep_time*backoff_multiplier)
        backoff_multiplier += 1
"""
