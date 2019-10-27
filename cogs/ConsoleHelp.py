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

        embed.add_field(name="To use a console name you must provide your name and platform surrounded in quotes.",
                        value="So for example a console player with the name `zombie killer` who plays on the "
                              "`Switch` would type their name as follows in the stats command.\n\n"
                              "`>>stats \"Zombie Killer Switch\"`\n\u200b", inline=False)

        embed.add_field(
            name="Now if you want to make your life easier I would recommend storing/linking your name to the "
                 "PaladinsAssistant.",
            value="You can do this by using the `>>console` command to look up your Paladins `player_id` and then"
                  "using the `>>store` command by doing `>>store your_player_id`. Then in commands you can just use "
                  "the word `me` in place of your console name and platform.\n\u200b", inline=False)

        embed.add_field(name="Below are the 3 steps (`with a picture`) of what you need to do if you are directed"
                             " to use Guru's site to find a console `player_id from the console command.`",
                        value="```md\n"
                              "1. Use the link generated from the command or go to https://paladins.guru/ and type "
                              "in the console player's name and then search.\n"
                              "2. Locate the account that you want and click on the name.\n"
                              "3. Then copy the number right before the player name.\n"
                              "4. Congrats you now have the console's players magical number.\n```", inline=False)

        embed.set_thumbnail(
            url="https://raw.githubusercontent.com/EthanHicks1/PaladinsAssistantBot/master/assets/Androxus.png")
        embed.set_image(
            url="https://raw.githubusercontent.com/EthanHicks1/PaladinsAssistantBot/master/assets/Console.png")
        embed.set_footer(text="If you still have questions feel free to message me @ FeistyJalapeno#9045. "
                              "I am a very busy but will try to respond when I can.")

        await ctx.send(embed=embed)


# Add this class to the cog list
def setup(bot):
    bot.add_cog(ConsoleHelp(bot))
