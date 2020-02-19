import discord
from discord.ext import commands


# For testing commands
class Testing(commands.Cog, name="Testing Commands"):
    """Testing Commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.command()
    async def testing(self, ctx):
        """
        info = ""
        for i in range(0, 20):
            td = await self.get_global_kda("FeistyJalapeno")
            info += str(td) + "\n"

        await ctx.send(info)
        """
        """
        for i in range(0, 10):
            embed = discord.Embed(
                description="Test limit: " + str(i+1) + "\nplayer's stats. ",
                colour=discord.colour.Color.dark_teal(),
            )
            await ctx.send(embed=embed)
        """
        """
        embed = discord.Embed(
            description="Someone's stats:\n Name: Bruh \n Winrate: 55%",
            colour=discord.colour.Color.dark_teal(),
        )
        await ctx.send(embed=embed)

        embed = discord.Embed(
            title="Some Title",
            description="Someone's stats:\n Name: Bruh \n Winrate: 55%",
            colour=discord.colour.Color.dark_teal(),
        )
        await ctx.send(embed=embed)

        embed = discord.Embed(
            title="`Someone's stats:`\n ```Name: Bruh``` \n Winrate: 55%",
            colour=discord.colour.Color.dark_teal(),
        )
        await ctx.send(embed=embed)
        """

        embed = discord.Embed(
            title="Some Title \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b "
                  "\u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b "
                  "\u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b ",
            colour=discord.colour.Color.dark_teal(),
        )
        embed.add_field(name="`Some Title`", value="Someone's stats:\nName: Bruh \nWinrate: 55%", inline=False)
        embed.add_field(name="```Some Title```", value="Derp:\nName: Dabber \nWinrate: 72.54%", inline=False)
        # embed.set_thumbnail(url=await helper.get_champ_image("Drogoz"))
        await ctx.send(embed=embed)

        return None


# Add this class to the cog list
def setup(bot):
    bot.add_cog(Testing(bot))
