import discord
from discord.ext import commands
from datetime import date
from datetime import datetime; datetime.now


# Class handles commands related to console players
class ConsoleCommands(commands.Cog, name="Console Commands"):
    """Console Commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='console', pass_context=True, ignore_extra=False, aliases=["Console"])
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def console(self, ctx, player_name, platform: str):
        async with ctx.channel.typing():
            platform = platform.lower()
            if platform == "xbox":
                platform = "10"
            elif platform == "ps4":
                platform = "9"
            elif platform == "switch":
                platform = "22"
            else:
                await ctx.send("```Invalid platform name. Valid platform names are:\n1. Xbox\n2. PS4\n3. Switch```")
                return None

            # players = paladinsAPI.getPlayerId(player_name, "steam")
            # players = paladinsAPI.getPlayerId(player_name, platform)

            players = self.bot.paladinsAPI.searchPlayers(player_name)

            if not players:
                await ctx.send("Found `0` players with the name `{}`.".format(player_name))
                return None

            # Hi-Rez endpoint down.
            if players is None:
                await ctx.send("A Hi-Rez endpoint is down meaning this command won't work. "
                               "Please don't try again for a while and give Hi-Rez a few hours to get the "
                               "endpoint online again.")
                return None

            players = [player for player in players if player.playerName.lower() == player_name.lower() and
                       player['portal_id'] == platform]
            num_players = len(players)
            if num_players > 20:  # Too many players...we must match case exactly
                await ctx.send("Found `{}` players with the name `{}`. Switching to case sensitive mode..."
                               .format(num_players, player_name))
                players = [player for player in players if player.playerName == player_name and
                           player['portal_id'] == platform]
                num_players = len(players)
                await ctx.send("Found `{}` players with the name `{}`."
                               .format(num_players, player_name))
                if num_players > 20:
                    await ctx.send("```There are too many players with the name {}:\n\nPlease look on PaladinsGuru to "
                                   "find the Player ID```https://paladins.guru/search?term={}&type=Player"
                                   .format(player_name, player_name))
                    return None

            ss = ""
            recent_player = []
            for player in players:
                ss += str(player) + "\n"
                player = self.bot.paladinsAPI.getPlayer(player=player.playerId)

                current_date = date.today()
                current_time = datetime.min.time()
                today = datetime.combine(current_date, current_time)
                last_seen = player.lastLoginDatetime
                last_seen = (today - last_seen).days

                # only add players seen in the last 90 days
                if last_seen <= 90:
                    recent_player.append(player)

            await ctx.send("Found `{}` recent player(s) `(seen in the last 90 days)`".format(len(recent_player)))
            for player in recent_player:
                current_date = date.today()
                current_time = datetime.min.time()
                today = datetime.combine(current_date, current_time)
                last_seen = player.lastLoginDatetime
                last_seen = (today - last_seen).days

                if last_seen <= 0:
                    last_seen = "Today"
                else:
                    last_seen = "{} days ago".format(last_seen)

                embed = discord.Embed(
                    title=player.playerName,
                    description="↓↓↓  Player ID  ↓↓↓```fix\n{}```".format(player.playerId),
                    colour=discord.colour.Color.dark_teal(),
                )
                embed.add_field(name='Last Seen:', value=last_seen, inline=True)
                embed.add_field(name='Account Level:', value=player.accountLevel, inline=True)
                embed.add_field(name='Hours Played:', value=player.hoursPlayed, inline=True)
                embed.add_field(name='Account Created:', value=player.createdDatetime, inline=True)
                await ctx.send(embed=embed)

    # Returns an embed of how to format a console name
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
    bot.add_cog(ConsoleCommands(bot))
