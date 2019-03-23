from discord.ext import commands


def server_owner_only():
    async def predicate(ctx):
        print("owner is:", ctx.guild.owner, ctx.author)
        if not ctx.guild.owner == ctx.author:
            raise NotServerOwner("Bruh you ain't the server owner. You can't use this command.")
        return True
    return commands.check(predicate)


class NotServerOwner(commands.CheckFailure):
    pass


# Class of commands that are solo (a.k.a) are not used/related to other functions
class SoloCommandCog(commands.Cog, name="Solo Commands"):
    """SoloCommandsCog"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='test2', aliases=['tt'])
    # @commands.is_owner() # This is bot owner
    @server_owner_only()
    async def test2(self, ctx):
        async with ctx.channel.typing():
            # print(ctx.channel.id, ctx.guild.id)
            # print("This server's id is:" + str(ctx.guild.id))
            await ctx.send("This server's id is: " + str(ctx.guild.id))


# Add this class to the cog list
def setup(bot):
    bot.add_cog(SoloCommandCog(bot))

