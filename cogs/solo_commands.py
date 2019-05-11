import discord
from discord.ext import commands
import json
import my_utils as helper
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO


def server_owner_only():
    async def predicate(ctx):
        if not ctx.guild.owner == ctx.author:
            raise NotServerOwner("Sorry you are not authorized to use this command. Only the server owner: " +
                                 str(ctx.guild.owner) + " can use this command")
        return True
    return commands.check(predicate)


class NotServerOwner(commands.CheckFailure):
    pass


# Class of commands that are solo (a.k.a) are not used/related to other functions
class SoloCommandCog(commands.Cog, name="Solo Commands"):
    """SoloCommandsCog"""
    # Different supported languages
    languages = ["Polish", "Português"]
    abbreviations = ["pl", "pt"]
    file_name = 'languages/server_configs'
    lan = []

    def __init__(self, bot):
        self.bot = bot
        self.load_lang()

    def load_lang(self):
        with open(self.file_name) as json_f:
            print("Loaded server languages")
            self.lan = json.load(json_f)

    @commands.command(name='prefix')
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
                await ctx.send("This bot is now set to use the prefix: `" + prefix + "` in this server")

    @commands.command(name='language')
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
                        # server_ids[str(ctx.guild.id)]["prefix"] = ">>"
                        server_ids[str(ctx.guild.id)]["lang"] = language
                    # need to update the file now
                    with open(self.file_name, 'w') as json_d:
                        json.dump(server_ids, json_d)
                    self.load_lang()  # Update the global/class list
                    helper.Lang.lan = server_ids  # Update the other class list
                await ctx.send("This bot is now set to use the language: `" + language + "` in this server")
            elif language == "reset":
                with open(self.file_name) as json_f:
                    server_ids = json.load(json_f)
                    server_ids.pop(str(ctx.guild.id), None)
                # need to update the file now
                with open(self.file_name, 'w') as json_d:
                    json.dump(server_ids, json_d)
                self.load_lang()  # Update the global/class list
                helper.Lang.lan = server_ids  # Update the other class list
                await ctx.send("Server language has been reset to English")
            else:
                lines = ""
                for abbr, lang, in zip(self.abbreviations, self.languages):
                    lines += "`" + abbr + ":` " + lang + "\n"
                await ctx.send("You entered an invalid language. The available languages are: \n" + lines +
                               "`reset: Resets the bot to use English"
                               "\nNote that by default the language is English so there is no need to set it to that.")
            # print(ctx.channel.id, ctx.guild.id)
            # print("This server's id is:" + str(ctx.guild.id))
            # await ctx.send("This server's id is: " + str(ctx.guild.id))

    @commands.command(name='check')
    async def check_server_language(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in self.lan:
            await ctx.send("this servers language is: " + self.lan[guild_id]["lang"])
            return self.lan[guild_id]["lang"]
        else:
            await ctx.send("this servers language is English")
            return "English"

    # Print how many times a person has used each command
    @commands.command(name='usage')
    async def usage(self, ctx):  # todo pick up here tomorrow
        user_commands = await helper.get_store_commands(ctx.author.id)
        message = ""
        for command, usage in user_commands.items():
            message += "{:9} {}\n".format(str(command), str(usage))
        await ctx.send('```'+message+'```')

        # Data to plot
        labels = 'Python', 'C++', 'Ruby', 'Java'
        sizes = [215, 130, 245, 210]
        colors = ['gold', 'yellowgreen', 'lightcoral', 'lightskyblue']
        explode = (0.1, 0, 0, 0)  # explode 1st slice

        # Plot
        plt.pie(sizes, explode=explode, labels=labels, colors=colors,
                autopct='%1.1f%%', shadow=True, startangle=140)

        plt.axis('equal')

        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        # im = Image.open(buf)
        # im.show()
        # buf.close()

        file = discord.File(filename="Deck.png", fp=buf)
        await ctx.send("```Enjoy the beautiful image below.```", file=file)


# Add this class to the cog list
def setup(bot):
    bot.add_cog(SoloCommandCog(bot))
