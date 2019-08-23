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


class PaladinsAssistant(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #
        self.load_bot_config()
        self.load_cogs()

        # Start the background tasks
        self.bg_task1 = self.loop.create_task(self.change_bot_presence())
        self.bg_task2 = self.loop.create_task(self.log_information())
        self.bg_task3 = self.loop.create_task(self.reset_uses())

    # Bot variables
    BOT_CONFIG = "token"

    BOT_STATUS = ">>help"
    TOKEN = ""
    PREFIX = ""

    BOT_AUTHOR = "FeistyJalapeno#9045"
    BOT_VERSION = "Version 1.0.0"
    GAME = ["Paladins", BOT_STATUS, BOT_VERSION, BOT_STATUS, "Features"]

    # Below cogs represents the folder our cogs are in. The dot is like an import path.
    INITIAL_EXTENSIONS = ['cogs.help', 'cogs.rand', 'cogs.PaladinsAPI', 'cogs.solo_commands']

    daily_error_count = 0
    daily_command_count = 0

    async def load_bot_config(self):
        # Gets token and prefix from a file
        with open(self.BOT_CONFIG, 'r') as f:
            self.TOKEN = f.readline().strip()
            self.PREFIX = f.readline().strip()
        f.close()

    # Launching the bot function
    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print('------')
        # global daily_command_count
        # daily_command_count = 0
        # global daily_error_count
        # daily_error_count = 0
        # client.loop.create_task(reset_uses())
        # client.loop.create_task(change_bot_presence())
        # if PREFIX != '&&':  # Prevents test bot from messing up bot stats log
        #    client.loop.create_task(log_information())
        await self.count_servers()
        print("Client is fully online and ready to go...")

    async def get_prefix(self, bot, message):
        default_prefix = [self.PREFIX]
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

    # We can use this code to track when people message this bot (a.k.a asking it commands)
    async def on_message(self, message):
        channel = message.channel
        # we do not want the bot to reply to itself
        if message.author == self.user:
            return

        # Seeing if someone is using the bot_prefix and calling a command
        if message.content.startswith(self.PREFIX):
            print(message.author, message.content, channel, message.guild, await helper.get_est_time())
            global daily_command_count
            daily_command_count = daily_command_count + 1
        # Seeing if someone is using the bot_prefix and calling a command
        if message.content.startswith(self.PREFIX + " "):
            msg = 'Oops looks like you have a space after the bot prefix {0.author.mention}'.format(message)
            try:  # First lets try to send the message to the channel the command was called
                await message.channel.send(msg)
            except BaseException:
                try:  # Next lets try to DM the message to the user
                    await message.author.send(msg)
                except BaseException:  # Bad sign if we end up here but is possible if the user blocks some DM's
                    print("The bot can't message the user in their DM's or in the channel they called the function.")

        # on_message has priority over function commands
        await self.process_commands(message)

    # Prints the number of servers the bot is in
    async def count_servers(self):
        await self.wait_until_ready()
        if not self.is_closed():
            print(Fore.GREEN + "Current servers:", Fore.MAGENTA + str(len(self.guilds)))
            print(Fore.GREEN + "Members in support server:", Fore.MAGENTA +
                  str(len(self.get_guild(554372822739189761).members)))

    # Changes bot presence every min
    async def change_bot_presence(self):
        secure_random = random.SystemRandom()
        await self.wait_until_ready()
        while not self.is_closed():
            await self.change_presence(status=discord.Status.dnd,  # Online, idle, invisible, dnd
                                         activity=discord.Game(name=secure_random.choice(self.GAME), type=0))
            await asyncio.sleep(60)  # Ever min

    # Here we load our extensions(cogs) listed above in [initial_extensions].
    def load_cogs(self):
        for extension in self.INITIAL_EXTENSIONS:
            try:
                super().load_extension(extension)
                print(Fore.GREEN + "Loaded extension:", Fore.MAGENTA + extension)
            except BaseException as e:
                print(Fore.RED + "Failed to load: {} because of {}".format(extension, e))
        print("")

    # Logs to a file server count, errors, commands used, api calls used (every 15 minutes to get a daily stats)
    async def log_information(self):
        await self.wait_until_ready()
        # sleep_time = await helper.get_second_until_hour()
        # await asyncio.sleep(sleep_time)
        while not self.is_closed():
            with open("log_file.csv", 'r') as r_log_file:
                date = await helper.get_est_time()
                date = date.split(" ")[1]

                lines = r_log_file.read().splitlines()
                servers, n1, old_errors, num_cmd, old_api_calls, old_date = lines[-1].split(',')
                api_calls = PaladinsAPI.paladinsAPI.getDataUsed()
                api_calls = api_calls.totalRequestsToday

                ss_c = str(len(self.get_guild(554372822739189761).members))

                # Updates tracked information for the current day or the next day
                if old_date.strip() == date:
                    lines[-1] = "{}, {}, {}, {}, {}, {}\n".format(len(self.guilds), ss_c, int(self.daily_error_count)
                                                                  + int(old_errors),
                                                                  int(self.daily_command_count) + int(num_cmd),
                                                                  api_calls, date)
                    with open("log_file.csv", 'w') as w_log_file:
                        w_log_file.write("\n".join(lines))
                else:
                    with open("log_file.csv", '+a') as a_log_file:
                        a_log_file.write(
                            "{}, {}, {}, {}, {}, {}\n".format(len(self.guilds), ss_c, int(self.daily_error_count),
                                                              self.daily_command_count, api_calls, date))
            self.daily_command_count = 0
            self.daily_error_count = 0
            print("Logged commands uses and server count: {}".format(await helper.get_est_time()))
            await asyncio.sleep(60 * 15)  # Log information every 15 mins

    # Resets command uses for -a on the current command at 6am everyday
    async def reset_uses(self):
        await self.wait_until_ready()
        sleep_time = await helper.get_seconds_until_reset()
        await asyncio.sleep(sleep_time)
        while not self.is_closed():
            await helper.reset_command_uses()
            updater = PaladinsAPI.PaladinsAPICog(self)
            for discord_id in os.listdir("user_data"):
                await updater.auto_update(discord_id)
            await asyncio.sleep(60 * 60 * 24)   # once per day

    # Bot tries to message the error in the channel where its caused and then tries to dm the error to the user
    async def send_error(self, cont, msg):
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

    # """
    # Handles errors when a user messes up the spelling or forgets an argument to a command or an error occurs
    async def on_command_error(self, ctx, error):
        # checks for non-discord command related errors
        if hasattr(error, "original"):
            # Catches connection related exceptions
            if isinstance(error.original, aiohttp_client_exceptions.ClientError) or isinstance(error.original,
                                                                                               gaierror) or \
                    isinstance(error.original, ConnectionError) or isinstance(error.original, TimeoutError) or \
                    isinstance(error.original, requests.exceptions.RequestException) or \
                    isinstance(error.original, concurrent.futures.TimeoutError):
                await self.send_error(cont=ctx, msg="Connection error. Please try again.")
                return None
            elif isinstance(error.original, discord.Forbidden):
                await self.send_error(cont=ctx, msg="The bot does not have permission to send messages in the channel:\n{}"
                                               "\n\n- where "
                                               "you just called the command:\n{}".format(ctx.channel,
                                                                                         ctx.message.content))
                return None
            elif isinstance(error.original, MemoryError):
                await self.send_error(cont=ctx,
                                 msg="Your lucky... you caused the bot to run out of memory. Don't worry though"
                                     "... the bot will recover. Please try again.")

            # Checking different types of ValueError (only closed file for now)
            elif isinstance(error.original, ValueError):
                if str(error.original) == "I/O operation on closed file.":
                    await self.send_error(cont=ctx,
                                     msg="The bot tried to send you a file/image but it has been taken away from"
                                         "the bot...probably because of an internet fluke. Please try again.")
                    return None

        # Checks for discord command errors
        if isinstance(error, commands.MissingRequiredArgument):
            await self.send_error(cont=ctx, msg="A required argument to the command you called is missing.")
        elif isinstance(error, commands.BadArgument):
            await self.send_error(cont=ctx, msg="Make sure the command is in the correct format.")
        elif isinstance(error, commands.errors.UnexpectedQuoteError):
            await self.send_error(cont=ctx, msg="If you are trying to type the name Mal`Damba please type his name as one "
                                           "word without any kinda of quote marks.")
        elif isinstance(error, commands.TooManyArguments):
            await self.send_error(cont=ctx, msg=error)
        elif isinstance(error, commands.CommandNotFound):
            msg = f"\N{WARNING SIGN} {error}"
            await self.send_error(cont=ctx, msg=msg)
        elif isinstance(error, commands.CommandOnCooldown):
            await self.send_error(cont=ctx, msg=error)
        elif isinstance(error, commands.MissingPermissions):
            await self.send_error(cont=ctx, msg=error)
        elif isinstance(error, commands.NotOwner):
            await self.send_error(cont=ctx, msg=error)
        elif isinstance(error, commands.CheckFailure):
            await self.send_error(cont=ctx, msg=error)
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

            msg = "Unfortunately, something really messed up. If you entered the command correctly just wait a few seconds" \
                  " and then try again. If the problem occurs again it is most likely a bug that will need be fixed."
            await self.send_error(cont=ctx, msg=msg)
    # """

# Creating client for bot
# client = Bot(command_prefix=get_prefix)
# client.remove_command('help')  # Removing default help command.


client = PaladinsAssistant()
# client.remove_command('help')

# Start the bot
client.run(client.TOKEN, bot=True, reconnect=True)
