import discord
from discord.ext import commands
from discord.ext.commands import Bot

from concurrent.futures import ThreadPoolExecutor

import asyncio

import PythonFunctions as Pf
import MyException as MyException

# Discord Variables
BOT_PREFIX = ("!!", ">>")
BOT_STATUS = "!!help or >>help"

BOT_AUTHOR = "FeistyJalapeno#9045"
BOT_VERSION = "Version 3.2.2 Beta"
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


# Get simple stats for a player's last amount of matches.
@client.command(name='history',
                pass_context=True)
async def history(ctx, player_name, amount=10):
    async with ctx.channel.typing():
        # Prevents blocking so that function calls are not delayed
        executor = ThreadPoolExecutor(max_workers=1)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(executor, Pf.get_history, player_name, amount)
        await ctx.send("```diff\n" + result + "```")


# Get stats for a player in their last match.
@client.command(name='last')
async def last(ctx, player_name, match_id=-1):
    # Prevents blocking so that function calls are not delayed
    executor = ThreadPoolExecutor(max_workers=1)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, Pf.get_last, player_name, match_id)
    # await client.say("```" + result + "```")
    await ctx.send(embed=result)


# Get stats for a player's current match.
@client.command(name='current',
                pass_context=True,
                aliases=['cur', 'c'])
async def current(ctx, player_name, option="-s"):
    # await client.send_typing(ctx.message.channel)
    async with ctx.channel.typing():
        # Prevents blocking so that function calls are not delayed
        executor = ThreadPoolExecutor(max_workers=1)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(executor, Pf.get_player_in_match, player_name, option)
        await ctx.send("```diff\n" + result + "```")


# Calls different random functions based on input
@client.command(name='rand',
                aliases=['random', 'r'])
async def rand(ctx, command):
    command = str(command).lower()
    embed = discord.Embed(
        colour=discord.colour.Color.dark_teal()
    )
    if command == "damage":
        champ = Pf.pick_damage()
        embed.add_field(name="Your random Damage champion is: ", value=champ)
        embed.set_thumbnail(url=Pf.get_champ_image(champ))
        # await client.say(embed=embed)
        await ctx.send(embed=embed)
    elif command == "flank":
        champ = Pf.pick_flank()
        embed.add_field(name="Your random Flank champion is: ", value=champ)
        embed.set_thumbnail(url=Pf.get_champ_image(champ))
        await ctx.send(embed=embed)
    elif command == "healer":
        champ = Pf.pick_support()
        embed.add_field(name="Your random Support/Healer champion is: ", value=champ)
        embed.set_thumbnail(url=Pf.get_champ_image(champ))
        await ctx.send(embed=embed)
    elif command == "tank":
        champ = Pf.pick_tank()
        embed.add_field(name="Your random FrontLine/Tank champion is: ", value=champ)
        embed.set_thumbnail(url=Pf.get_champ_image(champ))
        await ctx.send(embed=embed)
    elif command == "champ":
        champ = Pf.pick_random_champ()
        embed.add_field(name="Your random champion is: ", value=champ)
        embed.set_thumbnail(url=Pf.get_champ_image(champ))
        await ctx.send(embed=embed)
    elif command == "team":
        await ctx.send("Your random team is: \n" + "```css\n" + Pf.gen_team()+"```")
    elif command == "map" or command == "stage":
        await  ctx.send("Your random map is: " + "```css\n" + Pf.pick_map() + "```")
    else:
        await ctx.send("Invalid command. For the random command please choose from one following options: "
                       "damage, flank, healer, tank, champ, team, or map. "
                       "\n For example: `>>random damage` will pick a random damage champion")


# Returns simple stats based on the option they choose (champ_name, me, or elo)
@client.command(name='stats',
                aliases=['stat'])
async def stats(ctx, player_name, option="me", space=""):
    if space != "":
        option += " " + space
    else:  # If the user capitalize the option it cause a bug because if calls the wrong function
        option = option.lower()
    # Prevents blocking so that function calls are not delayed
    executor = ThreadPoolExecutor(max_workers=1)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, Pf.get_stats, player_name, option)
    if option == "me" or option == "elo":
        await ctx.send("```" + result + "```")
    else:
        await ctx.send(embed=result)


# Bot tries to message the error in the channel where its caused and then tries to dm the error to the user
@client.event
async def send_error(cont, msg):
    try:  # First lets try to send the message to the channel the command was called
        await cont.send(msg)
    except MyException:
        try:  # Next lets try to DM the message to the user
            # await client.send_message(cont.message.author, msg)
            await cont.send(msg)
        except MyException:  # Bad sign if we end up here but is possible if the user blocks some DM's
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
    # print(client.user.id)
    print('------')
    # Status of the bot
    global backoff_multiplier
    backoff_multiplier = 1
    # await client.change_presence(game=Game(name=BOT_STATUS, type=0), status='dnd')  # Online, idle, invisible, dnd
    await client.change_presence(status=discord.Status.dnd, activity=discord.Game(name=BOT_STATUS, type=0))
    print("Client is fully online and ready to go...")
    # await list_servers()

"""
async def list_servers():
    await client.wait_until_ready()
    while not client.is_closed:
        print("Current servers:", len(client.servers))
        # for server in client.servers:
        #    print(server.name)
        break
        # await asyncio.sleep(600)
"""

"""
# Changing bot presence changing
async def change_bot_presence():
    await client.wait_until_ready()
    secure_random = random.SystemRandom()
    while not client.is_closed:
        # await client.change_presence(game=Game(name=secure_random.choice(GAME), type=0), status='dnd')
        await asyncio.sleep(60)  # Ever min
"""


# Below cogs represents our folder our cogs are in. Following is the file name. So 'meme.py' in cogs, would be cogs.meme
# Think of it like a dot path import
initial_extensions = ['cogs.help']


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

# Does not work with discord rewrite
# client.loop.create_task(change_bot_presence())


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
