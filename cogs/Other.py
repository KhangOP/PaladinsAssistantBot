from discord.ext import commands
import my_utils as helper


# Class handles server configs. Allows a server owner to change the language or prefix of the bot in a server
class OtherCog(commands.Cog, name="Other Cog"):
    """OtherCog"""

    dashes = "----------------------------------------"

    def __init__(self, bot):
        self.bot = bot


# Print how many times a person has used each command
    @commands.command(name='usage', aliases=["użycie"])
    async def usage(self, ctx):
        user_commands = await helper.get_store_commands(ctx.author.id)
        len(user_commands)
        message = "Commands used by {}\n{}\n".format(ctx.author, self.dashes)

        # Data to plot
        labels = []
        data = []
        i = 1

        for command, usage in user_commands.items():
            message += "{}. {:9} {}\n".format(str(i), str(command), str(usage))
            labels.append(command)
            data.append(usage)
            i += 1

        await ctx.send('```md\n' + message + '```')


# Add this class to the cog list
def setup(bot):
    bot.add_cog(OtherCog(bot))
