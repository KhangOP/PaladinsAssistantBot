import discord
from discord.ext import commands
from pyrez.exceptions import PlayerNotFound, PrivatePlayer
import json
from colorama import Fore

import my_utils as helper


# All functions in this class use Pyrez wrapper to access Paladins API
class PaladinsAPICog(commands.Cog, name="Paladins API Commands"):
    """PaladinsAPICog"""

    def __init__(self, bot):
        self.bot = bot

    # Get the player id for a player based on their name. First it checks a dictionary and if they are not in there then
    # it does an API call to get the player's id. Then it writes that id to the dictionary. Helps save API calls.
    def get_player_id(self, player_name):
        if str(player_name).isnumeric():
            return player_name
        with open("player_ids") as json_f:
            player_ids = json.load(json_f)

        # This player is already in the dictionary and therefor we don't need to waste an api call to get the player id.
        if player_name in player_ids:
            return player_ids[player_name]
        else:
            original_name = player_name
            if " " not in player_name:
                try:
                    player = self.bot.paladinsAPI.getPlayer(player_name)
                except (PlayerNotFound, PrivatePlayer):
                    return -1  # invalid name
            else:  # Console name
                player_name, platform = player_name.rsplit(' ', 1)
                players = self.bot.paladinsAPI.searchPlayers(player_name)

                # New check
                if players is None:
                    return -1

                platform = platform.lower()
                if platform == "xbox":
                    platform = "10"
                elif platform == "ps4":
                    platform = "9"
                elif platform == "switch":
                    platform = "22"
                else:
                    return -2  # Invalid platform name.

                players = [player for player in players if player.playerName.lower() == player_name.lower() and
                           player['portal_id'] == platform]
                num_players = len(players)

                if num_players == 0:
                    return -1  # invalid name
                if num_players > 1:
                    return -3  # too many names (name overlap in switch)

                # The one player name
                player = players.pop()

            new_id = int(player.playerId)
            player_ids[original_name] = new_id  # store the new id in the dictionary

            # need to update the file now
            print("Added a new player the dictionary: " + player_name)
            with open("player_ids", 'w') as json_f:
                json.dump(player_ids, json_f)
            return new_id

    @staticmethod
    async def check_player_name(player_discord_id):
        with open("player_discord_ids") as json_f:
            player_discord_ids = json.load(json_f)

        # checking if the server stored their name
        if str(player_discord_id) in player_discord_ids:
            return player_discord_ids[str(player_discord_id)]
        else:
            return "None"

    # Calculates kda
    @classmethod
    async def calc_kda(cls, kills, deaths, assists):
        if assists != 0:
            assists = assists / 2
        if deaths == 0:  # Prefect KDA
            deaths = 1
        return str('{0:.2f}'.format(float(kills + assists) / deaths))

    # Calculates win rate
    # n1 = wins and n2 = total matches
    @classmethod
    async def calc_win_rate(cls, n1, n2):
        if n2 == 0:  # This means they have no data for the ranked split/season
            return "0"
        return str('{0:.2f}'.format((n1 / n2) * 100))

    # Uses Paladins API to get overall stats for a player
    async def get_player_stats_api(self, player_name, lang):
        # Player level, played hours, etc
        player_id = self.get_player_id(player_name)
        if player_id == -1:
            return self.bot.cmd_lang_dict["general_error2"][lang].format(player_name)
        elif player_id == -2:
            return "```Invalid platform name. Valid platform names are:\n1. Xbox\n2. PS4\n3. Switch```"
        elif player_id == -3:
            return "Name overlap detected. Please look up your Paladins ID using the `>>console` command."

        try:
            info = self.bot.paladinsAPI.getPlayer(player_id)
        except (PlayerNotFound, PrivatePlayer):
            return self.bot.cmd_lang_dict["general_error2"][lang].format(player_name)

        total = int(info.wins) + int(info.losses)

        # Adding in class stuff
        t_wins = 0
        t_loses = 0
        t_kda = 0
        count = 1

        stats = self.bot.paladinsAPI.getChampionRanks(player_id)
        if stats:  # if not None
            for stat in stats:
                wins = stat.wins
                losses = stat.losses
                kda = await self.calc_kda(stat.kills, stat.deaths, stat.assists)

                # Global win rate and kda
                if wins + losses > 10:  # Player needs to have over 20 matches with a champ for it to affect kda
                    t_wins += wins
                    t_loses += losses
                    t_kda += float(kda) * (wins + losses)  # These two lines allow the kda to be weighted
                    count += (wins + losses)  # aka the more a champ is played the more it affects global kda

            # Global win rate and kda
            wr = await self.calc_win_rate(t_wins, t_wins + t_loses)
            t_kda = str('{0:.2f}').format(t_kda / count)
        else:
            wr = await self.calc_win_rate(int(info.wins), total)
            t_kda = "???"

        # Overall Info
        ss = self.bot.cmd_lang_dict["stats_s1"][lang]
        ss = ss.format(self.bot.DASHES, str(info.playerName), str(info.accountLevel), wr, str(total), t_kda,
                       str(info.leaves))

        # Ranked Info
        s2 = self.bot.cmd_lang_dict["stats_s2"][lang]

        # Get the platform's ranked stats
        platform = str(info.platform).lower()
        if platform == "steam" or platform == "hirez":
            ranked = info.rankedKeyboard
        else:
            ranked = info.rankedController

        win = int(ranked.wins)
        lose = int(ranked.losses)
        wr = await self.calc_win_rate(win, win + lose)
        ss += s2.format(str(ranked.currentSeason), self.bot.DASHES, str(ranked.currentRank.getName()),
                        str(ranked.currentTrumpPoints), str(ranked.leaderboardIndex), wr, win, lose,
                        str(ranked.leaves))

        # Extra info
        s3 = self.bot.cmd_lang_dict["stats_s3"][lang]
        try:
            created = str(info.createdDatetime).split()[0]
        except IndexError:
            created = "Unknown"
        try:
            last = str(info.lastLoginDatetime).split()[0]
        except IndexError:
            last = "Unknown"
        ss += s3.format(self.bot.DASHES, created, last, str(info.platform), str(info.playedGods),
                        str(info.totalAchievements))
        return ss

    # maybe a combo of the mobile and non-mobile version
    async def get_player_stats_api_new(self, player_name, lang):
        # Player level, played hours, etc
        player_id = self.get_player_id(player_name)
        if player_id == -1:
            embed = discord.Embed(
                title=self.bot.cmd_lang_dict["general_error2"][lang].format(player_name),
                colour=discord.colour.Color.red()
            )
            return [embed]
        elif player_id == -2:
            embed = discord.Embed(
                title="```Invalid platform name. Valid platform names are:\n1. Xbox\n2. PS4\n3. Switch```",
                colour=discord.colour.Color.red()
            )
            return [embed]
        elif player_id == -3:
            embed = discord.Embed(
                title="Name overlap detected. Please look up your Paladins ID using the `>>console` command.",
                colour=discord.colour.Color.red()
            )
            return [embed]

        try:
            info = self.bot.paladinsAPI.getPlayer(player_id)
        except (PlayerNotFound, PrivatePlayer):
            embed = discord.Embed(
                description=self.bot.cmd_lang_dict["general_error2"][lang].format(player_name),
                colour=discord.colour.Color.red()
            )
            return [embed]

        embed = discord.Embed(
            title="Some Title \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b "
                  "\u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b "
                  "\u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b ",
            colour=discord.colour.Color.dark_teal(),
        )

        # Add in icon image
        embed.set_thumbnail(url=await helper.get_champ_image("Drogoz"))

        # Overall Info
        ss = self.bot.cmd_lang_dict["stats_s1"][lang]
        p1, p2 = ss.split("*")
        total = int(info.wins) + int(info.losses)
        wr = await self.calc_win_rate(int(info.wins), total)
        p2 = p2.format(str(info.playerName), str(info.accountLevel), wr, str(total), str(info.leaves))
        embed.add_field(name="**```{}```**".format(p1), value=p2, inline=False)

        # Ranked Info
        s2 = self.bot.cmd_lang_dict["stats_s2"][lang]

        # Get the platform's ranked stats
        platform = str(info.platform).lower()
        if platform == "steam" or platform == "hirez":
            ranked = info.rankedKeyboard
        else:
            ranked = info.rankedController

        win = int(ranked.wins)
        lose = int(ranked.losses)
        wr = await self.calc_win_rate(win, win + lose)
        p1, p2 = s2.split("*")
        p1 = p1.format(str(ranked.currentSeason))
        p2 = p2.format("`"+str(ranked.currentRank.getName()+"`"), str(ranked.currentTrumpPoints),
                       str(ranked.leaderboardIndex), wr, win, lose, str(ranked.leaves))
        embed.add_field(name="**```{}```**".format(p1), value=p2, inline=False)

        # Extra info
        s3 = self.bot.cmd_lang_dict["stats_s3"][lang]
        try:
            created = str(info.createdDatetime).split()[0]
        except IndexError:
            created = "Unknown"
        try:
            last = str(info.lastLoginDatetime).split()[0]
        except IndexError:
            last = "Unknown"

        p1, p2 = s3.split("*")
        p2 = p2.format(created, last, str(info.platform), str(info.playedGods), str(info.totalAchievements))
        embed.add_field(name="**```{}```**".format(p1), value=p2, inline=False)

        # print(ss, s2, s3)

        embeds = [embed]
        return embeds

    # Uses Paladins API to get overall stats for a player (Mobile version)
    async def get_player_stats_api_mobile(self, player_name, lang):
        # Player level, played hours, etc
        player_id = self.get_player_id(player_name)
        if player_id == -1:
            embed = discord.Embed(
                title=self.bot.cmd_lang_dict["general_error2"][lang].format(player_name),
                colour=discord.colour.Color.red()
            )
            return [embed]
        elif player_id == -2:
            embed = discord.Embed(
                title="```Invalid platform name. Valid platform names are:\n1. Xbox\n2. PS4\n3. Switch```",
                colour=discord.colour.Color.red()
            )
            return [embed]
        elif player_id == -3:
            embed = discord.Embed(
                title="Name overlap detected. Please look up your Paladins ID using the `>>console` command.",
                colour=discord.colour.Color.red()
            )
            return [embed]

        try:
            info = self.bot.paladinsAPI.getPlayer(player_id)
        except (PlayerNotFound, PrivatePlayer):
            embed = discord.Embed(
                description=self.bot.cmd_lang_dict["general_error2"][lang].format(player_name),
                colour=discord.colour.Color.red()
            )
            return [embed]

        # Adding in class stuff
        t_wins = 0
        t_loses = 0
        t_kda = 0
        count = 1

        stats = self.bot.paladinsAPI.getChampionRanks(player_id)
        total = int(info.wins) + int(info.losses)

        if stats:  # if not None
            for stat in stats:
                wins = stat.wins
                losses = stat.losses
                kda = await self.calc_kda(stat.kills, stat.deaths, stat.assists)

                # Global win rate and kda
                if wins + losses > 10:  # Player needs to have over 20 matches with a champ for it to affect kda
                    t_wins += wins
                    t_loses += losses
                    t_kda += float(kda) * (wins + losses)  # These two lines allow the kda to be weighted
                    count += (wins + losses)  # aka the more a champ is played the more it affects global kda

                # Global win rate and kda
            wr = await self.calc_win_rate(t_wins, t_wins + t_loses)
            t_kda = str('{0:.2f}').format(t_kda / count)

        else:
            wr = await self.calc_win_rate(int(info.wins), total)
            t_kda = "???"

        # Overall Info
        ss = self.bot.cmd_lang_dict["stats_s1"][lang + "_mobile"]
        ss = ss.format(str(info.playerName), str(info.accountLevel), wr, str(total), t_kda, str(info.leaves))

        parts = ss.split("\n")
        embed = discord.Embed(
            title="`{}  ------------`".format(parts.pop(0)),
            colour=discord.colour.Color.dark_teal(),
        )
        for part in parts:
            try:
                p1, p2 = part.split("*")
            except ValueError:
                p1 = "Error"
                p2 = "Error"
                print(parts, part)
                print(str(parts) + Fore.YELLOW, str(part) + Fore.YELLOW)
            embed.add_field(name=p1, value=p2, inline=False)

        # Ranked Info
        s2 = self.bot.cmd_lang_dict["stats_s2"][lang + "_mobile"]

        # Get the platform's ranked stats
        platform = str(info.platform).lower()
        if platform == "steam" or platform == "hirez":
            ranked = info.rankedKeyboard
        else:
            ranked = info.rankedController

        win = int(ranked.wins)
        lose = int(ranked.losses)
        wr = await self.calc_win_rate(win, win + lose)
        s2 = s2.format(str(ranked.currentRank.getName()),
                       str(ranked.currentTrumpPoints), str(ranked.leaderboardIndex), wr, win, lose, str(ranked.leaves))

        parts = s2.split("\n")
        embed2 = discord.Embed(
            title="`{} {}`".format(parts.pop(0), ranked.currentSeason),
            colour=discord.colour.Color.dark_magenta(),
        )
        for part in parts:
            p1, p2 = part.split("*")
            embed2.add_field(name=p1, value=p2, inline=False)

        # Extra info
        s3 = self.bot.cmd_lang_dict["stats_s3"][lang + "_mobile"]
        try:
            created = str(info.createdDatetime).split()[0]
        except IndexError:
            created = "Unknown"
        try:
            last = str(info.lastLoginDatetime).split()[0]
        except IndexError:
            last = "Unknown"

        s3 = s3.format(created, last, str(info.totalAchievements), str(info.platform), str(info.playedGods))

        parts = s3.split("\n")
        embed3 = discord.Embed(
            title="`{}  -------------`".format(parts.pop(0)),
            colour=discord.colour.Color.dark_teal(),
        )
        i = 0
        for part in parts:
            p1, p2 = part.split("*")
            if i != 2 and lang == "en":
                embed3.add_field(name=p1, value=p2, inline=True)
            else:
                embed3.add_field(name=p1, value=p2, inline=False)
            i += 1

        embeds = [embed, embed2, embed3]
        return embeds

    # Gets stats for a champ using Paladins API
    # Todo needed by the current command as well
    async def get_champ_stats_api(self, player_name, champ, simple, lang, mobile=False):
        # Gets player id and error checks
        player_id = self.get_player_id(player_name)
        if player_id == -1:
            if simple == 1:
                if mobile:
                    return [champ, "???", "???", "???"]
                ss = str('*   {:15} Lv. {:3}  {:7}   {:6}\n')
                ss = ss.format(champ, "???", "???", "???")
                return ss
            match_data = self.bot.cmd_lang_dict["general_error2"][lang].format(player_name)
            embed = discord.Embed(
                title=match_data,
                colour=discord.colour.Color.dark_teal()
            )
            return embed
        elif player_id == -2:
            if simple == 1:
                if mobile:
                    return [champ, "???", "???", "???"]
                ss = str('*   {:15} Lv. {:3}  {:7}   {:6}\n')
                ss = ss.format(champ, "???", "???", "???")
                return ss
            embed = discord.Embed(
                title="```Invalid platform name. Valid platform names are:\n1. Xbox\n2. PS4\n3. Switch```",
                colour=discord.colour.Color.red()
            )
            return embed
        elif player_id == -3:
            if simple == 1:
                if mobile:
                    return [champ, "???", "???", "???"]
                ss = str('*   {:15} Lv. {:3}  {:7}   {:6}\n')
                ss = ss.format(champ, "???", "???", "???")
                return ss
            embed = discord.Embed(
                title="Name overlap detected. Please look up your Paladins ID using the `>>console` command.",
                colour=discord.colour.Color.red()
            )
            return embed
        try:  # Todo Console name not returned in data (but correct)
            stats = self.bot.paladinsAPI.getChampionRanks(player_id)
            # {"Assists": 2771, "Deaths": 2058, "Gold": 880190, "Kills": 2444, "LastPlayed": "6/14/2019 9:49:51 PM",
            # "Losses": 125, "MinionKills": 253, "Minutes": 3527, "Rank": 58, "Wins": 144, "Worshippers": 33582898,
            # "champion": "Makoa", "champion_id": "2288", "player_id": "704972387", "ret_msg": null}
        except BaseException:
            if simple == 1:
                if mobile:
                    return [champ, "???", "???", "???"]
                ss = str('*   {:15} Lv. {:3}  {:7}   {:6}\n')
                ss = ss.format(champ, "???", "???", "???")
                return ss
            match_data = self.bot.cmd_lang_dict["general_error2"][lang].format(player_name)
            embed = discord.Embed(
                description=match_data,
                colour=discord.colour.Color.dark_teal()
            )
            return embed
        if stats is None:  # Private account
            if simple == 1:
                if mobile:
                    return [champ, "???", "???", "???"]
                ss = str('*{:18} Lv. {:3}  {:7}   {:6}\n')
                ss = ss.format(champ, "???", "???", "???")
                return ss
            match_data = self.bot.cmd_lang_dict["general_error"][lang].format(player_name)
            embed = discord.Embed(
                description=match_data,
                colour=discord.colour.Color.dark_teal()
            )
            return embed

        if "Mal" in champ:
            champ = "Mal'Damba"

        ss = ""
        t_wins = 0
        t_loses = 0
        t_kda = 0
        count = 1

        for stat in stats:
            wins = stat.wins
            losses = stat.losses
            kda = await self.calc_kda(stat.kills, stat.deaths, stat.assists)
            # champ we want to get the stats on
            if stat.godName == champ:
                win_rate = await self.calc_win_rate(wins, wins + losses)
                level = stat.godLevel

                last_played = str(stat.lastPlayed)
                if not last_played:  # Bought the champ but never played them
                    break

                ss = self.bot.cmd_lang_dict["stats_champ"][lang].replace("*", " ")

                ss = ss.format(champ, level, kda, stat.kills, stat.deaths, stat.assists,
                               win_rate, wins, losses, str(stat.lastPlayed).split()[0])
                if simple == 1:
                    if mobile:
                        return [champ, str(level), win_rate, kda]
                    win_rate += " %"
                    kda = "(" + kda + ")"
                    ss = str('*   {:15} Lv. {:3}  {:7}   {:6}\n')
                    ss = ss.format(champ, str(level), win_rate, kda)
                    """This Block of code adds color based on Win Rate"""
                    if "???" in win_rate:
                        pass
                    elif (float(win_rate.replace(" %", ""))) > 55.00:
                        ss = ss.replace("*", "+")
                    elif (float(win_rate.replace(" %", ""))) < 49.00:
                        ss = ss.replace("*", "-")
                    """^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"""
                    return ss

            # Global win rate and kda
            if wins + losses > 10:  # Player needs to have over 20 matches with a champ for it to affect kda
                t_wins += wins
                t_loses += losses
                t_kda += float(kda) * (wins + losses)  # These two lines allow the kda to be weighted
                count += (wins + losses)  # aka the more a champ is played the more it affects global kda

        # They have not played this champion yet
        if ss == "":
            ss = "No data for champion: " + champ + "\n"
            if simple == 1:
                ss = str('*{:18} Lv. {:3}  {:7}   {:6}\n')
                ss = ss.format(champ, "???", "???", "???")
                return ss
            embed = discord.Embed(
                description=ss,
                colour=discord.colour.Color.orange()
            )
            return embed

        # Global win rate and kda
        global_ss = str("\n\nGlobal KDA: {}\nGlobal Win Rate: {}% ({}-{})")
        win_rate = await self.calc_win_rate(t_wins, t_wins + t_loses)
        t_kda = str('{0:.2f}').format(t_kda / count)
        global_ss = global_ss.format(t_kda, win_rate, t_wins, t_loses)
        ss += global_ss

        # Create an embed
        my_title = player_name + "'s stats: "
        desc = "`{}`".format(ss)
        embed = discord.Embed(
            title=my_title,
            description=desc,
            colour=discord.colour.Color.dark_teal()
        )
        embed.set_thumbnail(url=await helper.get_champ_image(champ))
        return embed

    # Gets stats for a champ using Paladins API
    async def get_champ_stats_api_mobile(self, player_name, champ, lang):
        # Gets player id and error checks
        player_id = self.get_player_id(player_name)
        if player_id == -1:
            match_data = self.bot.cmd_lang_dict["general_error2"][lang].format(player_name)
            embed = discord.Embed(
                title=match_data,
                colour=discord.colour.Color.dark_teal()
            )
            return [embed]
        elif player_id == -2:
            embed = discord.Embed(
                title="```Invalid platform name. Valid platform names are:\n1. Xbox\n2. PS4\n3. Switch```",
                colour=discord.colour.Color.red()
            )
            return [embed]
        elif player_id == -3:
            embed = discord.Embed(
                title="Name overlap detected. Please look up your Paladins ID using the `>>console` command.",
                colour=discord.colour.Color.red()
            )
            return [embed]
        try:
            stats = self.bot.paladinsAPI.getChampionRanks(player_id)
        except BaseException:
            match_data = self.bot.cmd_lang_dict["general_error2"][lang].format(player_name)
            embed = discord.Embed(
                description=match_data,
                colour=discord.colour.Color.dark_teal()
            )
            return [embed]
        if stats is None:  # Private account
            match_data = self.bot.cmd_lang_dict["general_error"][lang].format(player_name)
            embed = discord.Embed(
                description=match_data,
                colour=discord.colour.Color.dark_teal()
            )
            return [embed]

        if "Mal" in champ:
            champ = "Mal'Damba"

        ss = ""
        t_wins = 0
        t_loses = 0
        t_kda = 0
        count = 1

        for stat in stats:
            wins = stat.wins
            losses = stat.losses
            kda = await self.calc_kda(stat.kills, stat.deaths, stat.assists)
            # champ we want to get the stats on
            if stat.godName == champ:
                win_rate = await self.calc_win_rate(wins, wins + losses)
                level = stat.godLevel

                last_played = str(stat.lastPlayed)
                if not last_played:  # Bought the champ but never played them
                    break

                ss = self.bot.cmd_lang_dict["stats_champ"][lang]

                ss = ss.format(champ, level, kda, stat.kills, stat.deaths, stat.assists,
                               win_rate, wins, losses, str(stat.lastPlayed).split()[0])

            # Global win rate and kda
            if wins + losses > 10:  # Player needs to have over 20 matches with a champ for it to affect kda
                t_wins += wins
                t_loses += losses
                t_kda += float(kda) * (wins + losses)  # These two lines allow the kda to be weighted
                count += (wins + losses)  # aka the more a champ is played the more it affects global kda

        # They have not played this champion yet
        if ss == "":
            ss = "No data for champion: " + champ + "\n"
            embed = discord.Embed(
                description=ss,
                colour=discord.colour.Color.orange()
            )
            return [embed]

        # Global win rate and kda
        t_kda = str('{0:.2f}').format(t_kda / count)
        win_rate = await self.calc_win_rate(t_wins, t_wins + t_loses)
        win_rate = '{}% ({}-{})'.format(win_rate, t_wins, t_loses)

        # Create an embed
        my_title = '`' + player_name + "'s stats: `"
        embed = discord.Embed(
            title=my_title,
            colour=discord.colour.Color.dark_teal()
        )
        embed.set_thumbnail(url=await helper.get_champ_image(champ))
        parts = ss.split("\n")
        for part in parts:
            p1, p2 = part.split("*")
            embed.add_field(name=p1, value=p2, inline=True)

        # Global stats
        embed2 = discord.Embed(
            title="`Global stats:`",
            colour=discord.colour.Color.dark_magenta(),
        )
        embed2.add_field(name='KDA:', value=t_kda, inline=True)
        embed2.add_field(name='Win Rate:', value=win_rate, inline=True)

        embeds = [embed, embed2]
        return embeds

    # Returns the highest or lowest stats sorted by different categories (Level, KDA, WL, Matches, Time)
    @commands.command(name='top', pass_context=True, ignore_extra=False, aliases=["Top", "bottom", "Bottom"])
    @commands.cooldown(3, 30, commands.BucketType.user)
    # Gets stats for a champ using Paladins API
    async def top(self, ctx, player_name, option, by_class="nope"):
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

        await helper.store_commands(ctx.author.id, "top")

        # Gets player id and error checks
        player_id = self.get_player_id(player_name)
        if player_id == -1:
            match_data = self.bot.cmd_lang_dict["general_error2"][lang].format(player_name)
            embed = discord.Embed(
                title=match_data,
                colour=discord.colour.Color.dark_teal()
            )
            return embed
        elif player_id == -2:
            embed = discord.Embed(
                title="```Invalid platform name. Valid platform names are:\n1. Xbox\n2. PS4\n3. Switch```",
                colour=discord.colour.Color.red()
            )
            return embed
        elif player_id == -3:
            embed = discord.Embed(
                title="Name overlap detected. Please look up your Paladins ID using the `>>console` command.",
                colour=discord.colour.Color.red()
            )
            return embed
        try:
            stats = self.bot.paladinsAPI.getChampionRanks(player_id)
        except BaseException:
            match_data = self.bot.cmd_lang_dict["general_error"][lang].format(player_name)
            embed = discord.Embed(
                description=match_data,
                colour=discord.colour.Color.dark_teal()
            )
            return embed
        if stats is None:  # Private account
            match_data = self.bot.cmd_lang_dict["general_error"][lang].format(player_name)
            embed = discord.Embed(
                description=match_data,
                colour=discord.colour.Color.dark_teal()
            )
            return embed

        player_champion_data = []
        count = 0

        mobile_status = await self.bot.get_mobile_status(ctx=ctx)

        for stat in stats:
            count += 1
            wins = stat.wins
            losses = stat.losses
            kda = await self.calc_kda(stat.kills, stat.deaths, stat.assists)

            # champ we want to get the stats on
            win_rate = float(await self.calc_win_rate(wins, wins + losses))
            level = stat.godLevel

            last_played = str(stat.lastPlayed)

            if last_played:  # Bought the champ but never played them
                player_champion_data.append([stat.godName, level, kda, win_rate, wins + losses, stat.json['Minutes']])

        # Convert option
        ordering = False if ctx.invoked_with in ["Bottom", "bottom"] else True

        # Converts key word to index in list
        index = {
            "level": 1,
            "kda": 2,
            "wl": 3,
            "matches": 4,
            "time": 5,
        }.get(option.lower(), -1)
        if index == -1:
            await ctx.send("```md\n Invalid option. Valid options are:\n1. {}\n2. {}\n3. {}\n4. {}\n5. {}```"
                           .format("Level", "KDA", "WL", "Matches", "Time"))
            return None

        player_champion_data = sorted(player_champion_data, key=lambda x: x[index], reverse=ordering)

        paladins_class_type = ["", "", "", ""]
        class_type_index = [0, 0, 0, 0]

        # non-mobile version
        if not mobile_status:
            for i, champ in enumerate(player_champion_data, start=0):
                champ = [str(j) for j in champ]  # convert all elements to string to make formatting easier
                hours = int(int(champ[5]) / 60)
                minutes = int(champ[5]) % 60
                champ[5] = "{}h {}m".format(hours, minutes)

                # Separate how the message will look
                if by_class == "class":
                    c_index = self.bot.champs.get_champ_class(champ[0])
                    class_type_index[c_index] += 1
                    if class_type_index[c_index] <= 9:
                        paladins_class_type[c_index] \
                            += "{}.  {:15}{:7} {:6} {:10} {:9} {:6}\n".format(class_type_index[c_index], *champ)
                    else:
                        paladins_class_type[c_index] \
                            += "{}. {:15}{:7} {:6} {:10} {:9} {:6}\n".format(class_type_index[c_index], *champ)
                else:
                    if i >= 9:
                        if i < 20:
                            paladins_class_type[0] += "{}. {:15}{:7} {:6} {:10} {:9} {:6}\n".format(i + 1, *champ)
                        else:
                            paladins_class_type[1] += "{}. {:15}{:7} {:6} {:10} {:9} {:6}\n".format(i + 1, *champ)
                    else:
                        paladins_class_type[0] += "{}.  {:15}{:7} {:6} {:10} {:9} {:6}\n".format(i + 1, *champ)

            if by_class == "class":
                message = "{:15}    {:7} {:6} {:10} {:9} {:6}\n{}\n" \
                    .format("Champion", "Level", "KDA", "Win Rate", "Matches", "Time(mins.)",
                            "------------------------------------------------------------------")
                await ctx.send("```md\n" + message + "#   Damage\n" + paladins_class_type[0] + "```")
                await ctx.send("```md\n" + message + "#   Flank\n" + paladins_class_type[1] + "```")
                await ctx.send("```md\n" + message + "#   Tank\n" + paladins_class_type[2] + "```")
                await ctx.send("```md\n" + message + "#   Support\n" + paladins_class_type[3] + "```")
            else:
                message = "{:15}    {:7} {:6} {:10} {:9} {:6}\n{}\n" \
                    .format("Champion", "Level", "KDA", "Win Rate", "Matches", "Time(mins.)",
                            "------------------------------------------------------------------")
                await ctx.send("```md\n" + message + paladins_class_type[0] + "```")
                if paladins_class_type[1] != "":
                    await ctx.send("```md\n" + paladins_class_type[1] + "```")
        # mobile compact version
        else:
            title_options = ["Champion", "Level", "KDA", "Win Rate", "Matches", "Time(mins.)"]
            if by_class == "class":
                class_title = ["{} ({})".format("Damage Champions", title_options[index]),
                               "{} ({})".format("Flank Champions", title_options[index]),
                               "{} ({})".format("Tank Champions", title_options[index]),
                               "{} ({})".format("Support Champions", title_options[index])]
                class_message = ["", "", "", ""]
                class_image = ["", "", "", ""]

                for i, champ in enumerate(player_champion_data, start=0):
                    c_index = self.bot.champs.get_champ_class(champ[0])
                    hours = int(int(champ[5]) / 60)
                    minutes = int(champ[5]) % 60
                    champ[5] = "{}h {}m".format(hours, minutes)
                    if class_message[c_index] == "":    # store the name of the highest champ per class
                        class_image[c_index] = champ[0]
                    class_message[c_index] += "{} ({})\n".format(champ[0], champ[index])

                for title, data, image in zip(class_title, class_message, class_image):
                    mobile_embed = discord.Embed(
                        title=title,
                        colour=discord.colour.Color.dark_teal(),
                        description=data
                    )

                    mobile_embed.set_thumbnail(url=await helper.get_champ_image(image))

                    await ctx.send(embed=mobile_embed)
            else:
                select_title = "{} ({})".format("Champion", title_options[index])

                new_value = ""

                for i, champ in enumerate(player_champion_data, start=0):
                    hours = int(int(champ[5]) / 60)
                    minutes = int(champ[5]) % 60
                    champ[5] = "{}h {}m".format(hours, minutes)
                    new_value += "{} ({})\n".format(champ[0], champ[index])

                mobile_embed = discord.Embed(
                    title=select_title,
                    colour=discord.colour.Color.dark_teal(),
                    description=new_value
                )

                mobile_embed.set_footer(text="If you would like to see more information then use this "
                                             "command on a non-mobile device. "
                                             "Limited to only show the option requested on mobile.")
                mobile_embed.set_thumbnail(url=await helper.get_champ_image(player_champion_data[0][0]))

                await ctx.send(embed=mobile_embed)

    # Returns simple stats based on the option they choose (champ_name, or me)
    @commands.command(name='stats', aliases=['Stats', 'statystyki', 'Statystyki', 'statistiques', 'Statistiques'],
                      pass_context=True, ignore_extra=False)
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def stats(self, ctx, player_name, option=None):
        lang = await self.bot.language.check_language(ctx=ctx)
        await helper.store_commands(ctx.author.id, "stats")

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

        # Checking for is_on_mobile() status
        mobile_status = await self.bot.get_mobile_status(ctx=ctx)

        # get basic player stats
        if option is None:
            if not mobile_status:
                result = await self.get_player_stats_api(player_name, lang=lang)
                await ctx.send("```md\n" + result + "```")
            else:
                embeds = await self.get_player_stats_api_mobile(player_name, lang=lang)
                # embeds = await self.get_player_stats_api_new(player_name, lang=lang)
                for embed in embeds:
                    await ctx.send(embed=embed)
        # get stats for a specific character
        else:
            champ_name = await helper.convert_champion_name_normal(option)
            if not mobile_status:
                result = await self.get_champ_stats_api(player_name, champ_name, simple=0, lang=lang)
                await ctx.send(embed=result)
            # mobile version
            else:
                embeds = await self.get_champ_stats_api_mobile(player_name, champ_name, lang=lang)
                for embed in embeds:
                    await ctx.send(embed=embed)


# Add this class to the cog list
def setup(bot):
    bot.add_cog(PaladinsAPICog(bot))
