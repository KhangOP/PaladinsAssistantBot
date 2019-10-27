import discord
from discord.ext import commands
import my_utils as helper


# Class handles server configs. Allows a server owner to change the language or prefix of the bot in a server
class ConsoleHelp(commands.Cog, name="Console Help"):
    """ConsoleHelp"""

    def __init__(self, bot):
        self.bot = bot


# Print how many times a person has used each command
    @commands.command(name='console_name')
    async def usage(self, ctx):
        embed = discord.Embed(
            title="How to format your console name in PaladinsAssistant.",
            colour=discord.Color.dark_teal(),
            description="\u200b"
        )

        embed.add_field(name="something", value="\u200b", inline=False)

        embed.set_thumbnail(url="https://raw.githubusercontent.com/EthanHicks1/PaladinsAssistantBot/master/assets/Androxus.png")
        embed.set_image(url="https://raw.githubusercontent.com/EthanHicks1/PaladinsAssistantBot/master/assets/Console.png")

        await ctx.send(embed=embed)


# Add this class to the cog list
def setup(bot):
    bot.add_cog(ConsoleHelp(bot))
