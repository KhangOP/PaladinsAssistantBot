import discord
from discord.ext import commands

from pyrez.exceptions import PlayerNotFound, PrivatePlayer, NotFound, MatchException


# Class handles commands related a player's previous matches
class MatchHistoryCommands(commands.Cog, name="Match History Commands"):
    """Match History Commands"""

    def __init__(self, bot):
        self.bot = bot

    @classmethod
    # Used to change text prefix to change it's color
    async def color_win_rates(cls, text, win_rate):
        if float(win_rate) > 60.0:
            return "+" + text
        elif float(win_rate) < 50.0 and float(win_rate) != 0.0:
            return "-" + text
        else:
            return "*" + text

    @classmethod
    # Converts the match name so that its small enough to fit on one line
    async def convert_match_type(cls, match_name):
        if "Practice" in match_name:
            return "Bot Match"
        elif "TDM" in match_name:
            return "TDM"
        elif "Onslaught" in match_name:
            return "Onslaught"
        elif "Ranked" in match_name:
            return "Ranked"
        elif "(KOTH)" in match_name:
            return "KOTH"
        elif "(Siege)" in match_name:  # Test Maps (WIP)
            return "Test Maps"
        else:
            return "Siege"

    @commands.command(name='history', pass_context=True, ignore_extra=False,
                      aliases=["History", "historia", "Historia"])
    @commands.cooldown(3, 40, commands.BucketType.user)
    async def history(self, ctx, player_name, amount=None, champ_name=None):
        lang = await self.bot.language.check_language(ctx=ctx)
        # Maybe convert the player name
        if str(player_name) == "me":
            player_name = await self.check_player_name(str(ctx.author.id))
        elif player_name[0] == "<" and player_name[1] == "@":  # 99% that someone has been mentioned
            player_name = player_name.replace("<", "").replace(">", "").replace("@", "").replace("!", "")
            if len(player_name) == 18:
                player_name = await self.check_player_name(player_name)

        if player_name == "None":
            await ctx.send("You have not stored your IGN yet. To do so please use the store command like so: "
                           "`>>store Paladins_IGN`")
            return None

        await helper.store_commands(ctx.author.id, "history")
        async with ctx.channel.typing():
            if amount:
                try:
                    amount = int(amount)
                except ValueError:
                    champ_name = amount
                    amount = 50
            else:
                amount = 10

            if amount > 50 or amount < 10:
                await ctx.send("Please enter an amount between 10-50.")
                await ctx.send("```fix\nDefaulting to the default value of 10 matches.```")
                amount = 10
            player_id = self.get_player_id(player_name)
            if player_id == -1:
                await ctx.send(self.lang_dict["general_error2"][lang].format(player_name))
                return None
            elif player_id == -2:
                await ctx.send("```Invalid platform name. Valid platform names are:\n1. Xbox\n2. PS4\n3. Switch```")
                return None
            elif player_id == -3:
                await ctx.send("Name overlap detected. Please look up your Paladins ID using the `>>console` command.")
                return None

            if champ_name:  # Check in case they don't provide champ name
                champ_name = await self.convert_champion_name(str(champ_name))

            try:
                paladins_data = self.bot.paladinsAPI.getMatchHistory(player_id)
                # Endpoint down
                if paladins_data is None:
                    await ctx.send("```fix\nPaladins Endpoint down (no data returned). Please try again later and "
                                   "hopefully by then Evil Mojo will have it working again.```")
                    return None
            except (NotFound, MatchException):
                await ctx.send("Player does not have recent match data or their account is private. Make sure the first"
                               " parameter is a player name and not the Match Id.")
                return None

            count = 0
            total_matches = 0
            match_data = ""
            match_data2 = ""
            # Damage, Flank, Tank, Support => (win, lose)
            total_wins = [0, 0, 0, 0, 0, 0, 0, 0]
            # Damage, Flank, Tank, Support => (kda, total_matches per class)
            total_kda = [0, 0, 0, 0, 0, 0, 0, 0]
            global_kda = 0.0
            for match in paladins_data:
                # Check to see if this player does have match history
                if match.playerName is None:
                    await ctx.send("Player does not have recent match data or their account is private.")
                    return None
                else:
                    player_name = match.playerName

                # empty string means to get everything or only get matches with a certain champ
                if not champ_name or champ_name == match.godName:
                    ss = str('+{:10}{:4}{:3}:00 {:9} {:9} {:5} ({}/{}/{})\n')
                    kills = match.kills
                    deaths = match.deaths
                    assists = match.assists
                    kda = await self.calc_kda(kills, deaths, assists)
                    match_name = await self.convert_match_type(match.mapName)
                    ss = ss.format(match.godName, match.winStatus, match.matchMinutes, match_name,
                                   match.matchId, kda, kills, deaths, assists)

                    # we don't want to count event or bot matches when calculating stats
                    if match_name != "Bot Match" and match_name != "End Times" and match_name != "Test Maps":
                        global_kda += float(kda)
                        total_matches += 1
                        class_index = self.bot.champs.get_champ_class(match.godName)
                        if class_index != -1:
                            total_kda[class_index * 2] += float(kda)
                            total_kda[class_index * 2 + 1] += 1
                            if match.winStatus == "Loss":
                                total_wins[class_index * 2 + 1] += 1  # Losses
                            else:
                                total_wins[class_index * 2] += 1  # Wins
                        else:
                            print("Unclassified champion: " + str(match.godName))

                    # Used for coloring
                    if match.winStatus == "Loss":
                        ss = ss.replace("+", "-")

                    if count >= 30:
                        match_data2 += ss
                    else:
                        match_data += ss

                # Making sure we display the correct number of matches
                count += 1
                if count == amount:
                    break

            if not match_data and champ_name:
                await ctx.send("Could not find any matches with the champion: `" + champ_name + "` in the last `"
                               + str(amount) + "` matches.")
                return None

            # Base string to hold kda and win rate for all classes
            ss = "Class      KDA:  Win Rate:\n\n" \
                 "Total:   {:5}  {:6}% ({}-{})\n" \
                 "Damages: {:5}  {:6}% ({}-{})\n" \
                 "Flanks:  {:5}  {:6}% ({}-{})\n" \
                 "Tanks:   {:5}  {:6}% ({}-{})\n" \
                 "Healers: {:5}  {:6}% ({}-{})\n\n"

            # Calculating win rates
            d_t = total_wins[0] + total_wins[1]  # Damage total matches
            f_t = total_wins[2] + total_wins[3]  # Flank total matches
            t_t = total_wins[4] + total_wins[5]  # Tank total matches
            s_t = total_wins[6] + total_wins[7]  # Healer total matches
            d_wr = await self.calc_win_rate(total_wins[0], d_t)
            f_wr = await self.calc_win_rate(total_wins[2], f_t)
            t_wr = await self.calc_win_rate(total_wins[4], t_t)
            s_wr = await self.calc_win_rate(total_wins[6], s_t)

            # Total wins/loses
            if total_matches == 0:  # prevent division by 0
                total_matches = 1
            global_kda = round(global_kda / total_matches, 2)
            tot_wins = total_wins[0] + total_wins[2] + total_wins[4] + total_wins[6]
            tot_loses = total_wins[1] + total_wins[3] + total_wins[5] + total_wins[7]
            total_wr = await self.calc_win_rate(tot_wins, d_t + f_t + t_t + s_t)

            # Coloring based off of class/total win rates
            ss = ss.replace("Total", await self.color_win_rates("Total", total_wr)) \
                .replace("Damages", await self.color_win_rates("Damages", d_wr)) \
                .replace("Flanks", await self.color_win_rates("Flanks", f_wr)) \
                .replace("Tanks", await self.color_win_rates("Tanks", t_wr)) \
                .replace("Healers", await self.color_win_rates("Healers", s_wr))

            # KDA calc
            d_kda, f_kda, t_kda, s_kda, = 0.0, 0.0, 0.0, 0.0
            if total_kda[0] != 0:
                d_kda = round(total_kda[0] / total_kda[1], 2)
            if total_kda[2] != 0:
                f_kda = round(total_kda[2] / total_kda[3], 2)
            if total_kda[4] != 0:
                t_kda = round(total_kda[4] / total_kda[5], 2)
            if total_kda[6] != 0:
                s_kda = round(total_kda[6] / total_kda[7], 2)

            # Filling the the string with all the data
            ss = ss.format(global_kda, total_wr, tot_wins, tot_loses, d_kda, d_wr, total_wins[0], total_wins[1], f_kda,
                           f_wr, total_wins[2], total_wins[3], t_kda, t_wr, total_wins[4], total_wins[5], s_kda, s_wr,
                           total_wins[6], total_wins[7])

            title = str('{}\'s last {} matches:\n\n').format(str(player_name), count)
            title += str('{:11}{:4}  {:4} {:9} {:9} {:5} {}\n').format("Champion", "Win?", "Time", "Mode", "Match ID",
                                                                       "KDA", "Detailed")
            title += match_data
        await ctx.send("```diff\n" + title + "```")
        match_data2 += "\n\n" + ss
        await ctx.send("```diff\n" + match_data2 + "```")

    # Returns simple match history details
    @commands.command(name='last', pass_context=True, ignore_extra=False, aliases=["Last", "ostatni", "Ostatni"])
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def last(self, ctx, player_name, match_id=-1):
        lang = await self.bot.language.check_language(ctx=ctx)
        # Maybe convert the player name
        if str(player_name) == "me":
            player_name = await self.check_player_name(str(ctx.author.id))
        elif player_name[0] == "<" and player_name[1] == "@":  # 99% that someone has been mentioned
            player_name = player_name.replace("<", "").replace(">", "").replace("@", "").replace("!", "")
            if len(player_name) == 18:
                player_name = await self.check_player_name(player_name)

        if player_name == "None":
            await ctx.send("You have not stored your IGN yet. To do so please use the store command like so: "
                           "`>>store Paladins_IGN`")
            return None

        await helper.store_commands(ctx.author.id, "last")
        player_id = self.get_player_id(player_name)

        if player_id == -1:
            match_data = self.lang_dict["general_error2"][lang].format(player_name)
            embed = discord.Embed(
                title=match_data,
                colour=discord.colour.Color.dark_teal()
            )
            await ctx.send(embed=embed)
            return None
        elif player_id == -2:
            embed = discord.Embed(
                title="```Invalid platform name. Valid platform names are:\n1. Xbox\n2. PS4\n3. Switch```",
                colour=discord.colour.Color.red()
            )
            await ctx.send(embed=embed)
            return None
        elif player_id == -3:
            embed = discord.Embed(
                title="Name overlap detected. Please look up your Paladins ID using the `>>console` command.",
                colour=discord.colour.Color.red()
            )
            await ctx.send(embed=embed)
            return None

        try:
            paladins_data = self.bot.paladinsAPI.getMatchHistory(player_id)

            # Endpoint down
            if paladins_data is None:
                await ctx.send("```fix\nPaladins Endpoint down (no data returned). Please try again later and "
                               "hopefully by then Evil Mojo will have it working again.```")
                return None
        except (NotFound, MatchException):
            await ctx.send("Player does not have recent match data or their account is private. Make sure the first"
                           " parameter is a player name and not the Match Id.")
            return None

        for match in paladins_data:
            # Check to see if this player does have match history
            if match.playerName is None:
                break

            if match_id == -1 or match_id == match.matchId:
                match_data = str('{}\'s {} match:\n\n').format(str(match.playerName),
                                                               str(match.mapName).replace("LIVE", ""))
                ss = str('`Match Status: {} ({} mins)\nChampion: {}\nKDA: {} ({}-{}-{})\nDamage: {:,}\nDamage Taken: '
                         '{:,}\nHealing: {:,}\nSelf Healing: {:,}\nObjective Time: {}\nShielding: {:,}`\n')
                kills = match.kills
                deaths = match.deaths
                assists = match.assists
                kda = await self.calc_kda(kills, deaths, assists)
                match_data += ss.format(match.winStatus, match.matchMinutes, match.godName, kda, kills, deaths, assists,
                                        match.damage, match.damageTaken, match.healing, match.healingPlayerSelf,
                                        match.objectiveAssists, match.damageMitigated)

                embed = discord.Embed(
                    description=match_data,
                    colour=discord.colour.Color.dark_teal(),
                )

                embed.set_thumbnail(url=await helper.get_champ_image(match.godName))

                map_name = match.mapName.replace("LIVE ", "").replace("Ranked ", "").replace(" (TDM)", "") \
                    .replace(" (Onslaught) ", "").replace(" (Siege)", "").replace("Practice ", "").lower() \
                    .replace(" ", "_").replace("'", "")
                map_url = "https://raw.githubusercontent.com/EthanHicks1/PaladinsAssistantBot/master/icons/maps/{}.png" \
                    .format(map_name)
                embed.set_image(url=map_url)

                await ctx.send(embed=embed)
                return None

        # If the match id could not be found
        embed = discord.Embed(
            description="Could not find a match with the match id: " + str(match_id),
            colour=discord.colour.Color.dark_teal()
        )

        # If player has not played recently
        if match_id == -1:
            embed.description = "Player does not have recent match data or their account is private."

        await ctx.send(embed=embed)


# Add this class to the cog list
def setup(bot):
    bot.add_cog(MatchHistoryCommands(bot))
