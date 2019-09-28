from discord.ext import commands
import json
from colorama import Fore


# Function decoder that only allows server owns to use a certain command
def server_owner_only():
    async def predicate(ctx):
        # If in dm's
        if ctx.guild is None:
            return True
        if not ctx.guild.owner == ctx.author:
            raise NotServerOwner("Sorry you are not authorized to use this command. Only the server owner: " +
                                 str(ctx.guild.owner) + " can use this command")
        return True
    return commands.check(predicate)


class NotServerOwner(commands.CheckFailure):
    pass


# Class handles server configs. Allows a server owner to change the language or prefix of the bot in a server
class ServersConfigCog(commands.Cog, name="Servers Config"):
    """ServersConfigCog"""
    # Different supported languages
    languages = ["Polish", "Português"]
    abbreviations = ["pl", "pt"]

    file_name = ''
    lan = {}

    def __init__(self, bot):
        self.bot = bot

        self.lan = self.bot.servers_config
        self.file_name = self.bot.BOT_SERVER_CONFIG_FILE

    # Triggers a reload of the server configs json file and then updates this cogs json as well
    def reload_server_conf(self):
        print(Fore.CYAN + "Reloading server configs...")
        self.bot.load_bot_servers_config()
        self.lan = self.bot.servers_config

    @commands.command(name='prefix')
    @commands.guild_only()
    @server_owner_only()
    async def set_server_prefix(self, ctx, prefix):
        async with ctx.channel.typing():
            with open(self.file_name) as json_f:
                server_ids = json.load(json_f)
                try:
                    server_ids[str(ctx.guild.id)]["prefix"] = prefix
                except KeyError:  # Server has no configs yet
                    server_ids[str(ctx.guild.id)] = {}
                    server_ids[str(ctx.guild.id)]["prefix"] = prefix
                    # server_ids[str(ctx.guild.id)]["lang"] = "en"
                with open(self.file_name, 'w') as json_d:
                    json.dump(server_ids, json_d)
                self.reload_server_conf()  # Update the main bots json
                await ctx.send("This bot is now set to use the prefix: `" + prefix + "` in this server")

    @commands.command(name='language', aliases=["język"])
    @commands.guild_only()
    @server_owner_only()
    async def set_server_language(self, ctx, language: str):
        async with ctx.channel.typing():
            language = language.lower()

            if language in self.abbreviations:
                with open(self.file_name) as json_f:
                    server_ids = json.load(json_f)
                    try:
                        server_ids[str(ctx.guild.id)]["lang"] = language  # store the server id in the dictionary
                    except KeyError:  # Server has no configs yet
                        server_ids[str(ctx.guild.id)] = {}
                        server_ids[str(ctx.guild.id)]["lang"] = language
                    # need to update the file now
                    with open(self.file_name, 'w') as json_d:
                        json.dump(server_ids, json_d)
                    self.reload_server_conf()  # Update the main bots json
                await ctx.send("This bot is now set to use the language: `" + language + "` in this server")
            elif language == "reset":
                with open(self.file_name) as json_f:
                    server_ids = json.load(json_f)
                    server_ids[str(ctx.guild.id)].pop("lang", None)
                # need to update the file now
                with open(self.file_name, 'w') as json_d:
                    json.dump(server_ids, json_d)
                self.reload_server_conf()  # Update the main bots json

                await ctx.send("Server language has been reset to English")
            else:
                lines = ""
                for abbr, lang, in zip(self.abbreviations, self.languages):
                    lines += "`" + abbr + ":` " + lang + "\n"
                await ctx.send("You entered an invalid language. The available languages are: \n" + lines +
                               "`reset:` Resets the bot to use English"
                               "\nNote that by default the language is English so there is no need to set it to that.")
            # print(ctx.channel.id, ctx.guild.id)
            # print("This server's id is:" + str(ctx.guild.id))
            # await ctx.send("This server's id is: " + str(ctx.guild.id))

    @commands.command(name='check')
    async def check_server_language(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in self.lan and "lang" in self.lan[guild_id]:
            await ctx.send("This server's language is: " + self.lan[guild_id]["lang"])
            return self.lan[guild_id]["lang"]
        else:
            await ctx.send("This server's language is English")
            return "English"


# Add this class to the cog list
def setup(bot):
    bot.add_cog(ServersConfigCog(bot))
