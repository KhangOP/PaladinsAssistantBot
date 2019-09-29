import discord
from discord.ext import commands
import my_utils as helper
from datetime import datetime; datetime.now
from datetime import date


from pyrez.exceptions import PlayerNotFound
from pyrez.exceptions import NotFound
import aiohttp

import json
from psutil import Process
from os import getpid

from colorama import Fore


# All functions in this class use Pyrez wrapper to access Paladins API
class PaladinsAPICog(commands.Cog, name="Paladins API Commands"):
    """PaladinsAPICog"""

    def __init__(self, bot):
        self.bot = bot
        self.load_lang()

    DAMAGES = ["Cassie", "Kinessa", "Drogoz", "Bomb King", "Viktor", "Sha Lin", "Tyra", "Willo", "Lian", "Strix",
               "Vivian", "Dredge", "Imani"]
    FLANKS = ["Skye", "Buck", "Evie", "Androxus", "Maeve", "Lex", "Zhin", "Talus", "Moji", "Koga"]
    TANKS = ["Barik", "Fernando", "Ruckus", "Makoa", "Torvald", "Inara", "Ash", "Terminus", "Khan", "Atlas"]
    SUPPORTS = ["Grohk", "Grover", "Ying", "Mal Damba", "Seris", "Jenos", "Furia", "Pip", "Io"]

    dashes = "----------------------------------------"

    lang_dict = {}
    file_name = "languages/paladins_api_lang_dict"

    def load_lang(self):
        # Loads in language dictionary (need encoding option so it does not mess up other languages)
        with open(self.file_name, encoding='utf-8') as json_f:
            print(Fore.CYAN + "Loaded language dictionary for PaladinsAPICog...")
            self.lang_dict = json.load(json_f)

    # Returns a number for indexing in a list
    @classmethod
    def get_champ_class(cls, champ_name: str):
        champ_name = champ_name.title()
        if champ_name in cls.DAMAGES:
            return 0
        elif champ_name in cls.FLANKS:
            return 1
        elif champ_name in cls.TANKS:
            return 2
        elif champ_name in cls.SUPPORTS:
            return 3
        else:
            return -1

    @classmethod
    async def color_win_rates(cls, text, win_rate):
        if float(win_rate) > 60.0:
            return "+" + text
        elif float(win_rate) < 50.0 and float(win_rate) != 0.0:
            return "-" + text
        else:
            return "*" + text

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
                except PlayerNotFound:
                    return -1  # invalid name
            else:  # Console name
                player_name, platform = player_name.rsplit(' ', 1)
                players = self.bot.paladinsAPI.searchPlayers(player_name)

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
        elif "End Times" in match_name or "Crazy King" in match_name:  # Event name
            return "End Times"
        elif "(Siege)" in match_name:  # Test Maps (WIP Thrones)
            return "Test Maps"
        else:
            return "Siege"

    @classmethod
    # Converts champion names to include spacing in the name if needed
    async def convert_champion_name(cls, champ_name: str):
        champ_name = champ_name.title()
        # These are the special cases that need to be checked
        if "Bomb" in champ_name:
            return "Bomb King"
        if "Mal" in champ_name:
            return "Mal Damba"
        if "Sha" in champ_name:
            return "Sha Lin"
        # else return the name passed in since its already correct
        return champ_name

    # Gets KDA and Win Rate for a player from Nonsocial's herokuapp
    async def get_global_kda(self, player_id):
        url = "http://nonsocial.herokuapp.com/api/kda?player=" + str(player_id)
        async with aiohttp.ClientSession(conn_timeout=5, read_timeout=5) as cs:
            async with cs.get(url) as r:
                soup = await r.text()  # returns dict

                # Error checking to make sure that the player was found on the site
                if 'ERROR' in soup:
                    error = ["Private Account", "???", "???", "???"]
                    return error

                # Stop being an asshole. It was supposed to be free and unlimited, Y'all are paying nothing and it's
                # online 24/7 almost 1 year (8/2018). But because some shitty viewers are spamming stupid invalid
                # inputs such as !rank Nightbot, !rank SadMartini all endpoints are limited to 15 calls per minute.

                # Checking to see if we have used up the 15 calls per min
                if 'Stop being an asshole.' in soup:
                    try:
                        data = await self.get_player_current_stats_api(player_id)
                    except BaseException:
                        data = ["Private Account", "???", "???", "???"]
                    return data
                # FeistyJalapeno (Level 710): 5740 Wins, 3475 Losses
                #  (Kills: 114,019 / Deaths: 63,976 / Assists: 108,076 - 2.63 KDA) - Win rate: 62.29%

                split1 = soup.split("(Level ")

                try:
                    player_name = str(split1[0]).strip()  # Player Name
                except BaseException:
                    print(Fore.RED + str(soup))
                    return ["Connection Error", "???", "???", "???"]
                try:
                    level = split1[1].split(")")[0]  # Level
                    temp = int(level)
                except (ValueError, IndexError, BaseException) as e:
                    level = "???"
                    print(Fore.LIGHTCYAN_EX + "???? what in the string nation is going on: " + Fore.YELLOW + soup)
                    print(e)
                try:
                    kda = split1[1].split("- ")[1].split(" KDA")[0]  # KDA
                    temp = float(kda)
                except (ValueError, IndexError, BaseException) as e:
                    kda = "???"
                    print(Fore.LIGHTCYAN_EX + "???? what in the string nation is going on: " + Fore.YELLOW + soup)
                    print(e)
                try:
                    win_rate = soup.split("Win rate: ")[1].split("%")[0]  # Win Rate
                    temp = float(win_rate)
                except (ValueError, IndexError, BaseException) as e:
                    win_rate = "???"
                    print(Fore.LIGHTCYAN_EX + "???? what in the string nation is going on: " + Fore.YELLOW + soup)
                    print(e)

                stats = [player_name, level, win_rate, kda]

                return stats

    # Current command helper function
    async def get_player_current_stats_api(self, player_name):
        # Player level, Account level, Win Rate
        player_id = self.get_player_id(player_name)
        if player_id == -1:
            return ["Private Account", "???", "???", "???"]
        try:
            info = self.bot.paladinsAPI.getPlayer(player_id)
        except PlayerNotFound:
            return ["Private Account", "???", "???", "???"]

        # Overall Info
        total = int(info.wins) + int(info.losses)
        wr = await self.calc_win_rate(int(info.wins), total)

        # Get KDA
        try:
            stats = self.bot.paladinsAPI.getChampionRanks(player_id)
        except BaseException:
            return ["Private Account", "???", "???", "???"]
        if stats is None:  # Private account
            return ["Private Account", "???", "???", "???"]

        t_wins = 0
        t_loses = 0
        t_kda = 0
        count = 1

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

        kda = str('{0:.2f}').format(t_kda / count)

        return [str(info.playerName), str(info.accountLevel), wr, kda]

    # Uses Paladins API to get overall stats for a player
    async def get_player_stats_api(self, player_name, lang):
        # Player level, played hours, etc
        player_id = self.get_player_id(player_name)
        if player_id == -1:
            return self.lang_dict["general_error2"][lang].format(player_name)
        elif player_id == -2:
            return "```Invalid platform name. Valid platform names are:\n1. Xbox\n2. PS4\n3. Switch```"
        elif player_id == -3:
            return "Name overlap detected. Please look up your Paladins ID using the `>>console` command."

        try:
            info = self.bot.paladinsAPI.getPlayer(player_id)
        except PlayerNotFound:
            return self.lang_dict["general_error2"][lang].format(player_name)

        # if info.createdDatetime == "":
        #    print(info.accountLevel, info.wins, info.playerName, info.platform)

        # Overall Info
        ss = self.lang_dict["stats_s1"][lang]
        total = int(info.wins) + int(info.losses)
        wr = await self.calc_win_rate(int(info.wins), total)
        ss = ss.format(self.dashes, str(info.playerName), str(info.accountLevel), wr, str(total), str(info.leaves))

        # Ranked Info
        s2 = self.lang_dict["stats_s2"][lang]

        # Get the platform's ranked stats
        platform = str(info.platform).lower()
        if platform == "steam" or platform == "hirez":
            ranked = info.rankedKeyboard
        else:
            ranked = info.rankedController

        win = int(ranked.wins)
        lose = int(ranked.losses)
        wr = await self.calc_win_rate(win, win + lose)
        ss += s2.format(str(ranked.currentSeason), self.dashes, str(ranked.currentRank.getName()),
                        str(ranked.currentTrumpPoints), str(ranked.leaderboardIndex), wr, win, lose,
                        str(ranked.leaves))

        # Extra info
        s3 = self.lang_dict["stats_s3"][lang]
        try:
            created = str(info.createdDatetime).split()[0]
        except IndexError:
            created = "Unknown"
        try:
            last = str(info.lastLoginDatetime).split()[0]
        except IndexError:
            last = "Unknown"
        ss += s3.format(self.dashes, created, last, str(info.platform), str(info.playedGods),
                        str(info.totalAchievements))
        return ss

    # Uses Paladins API to get overall stats for a player (Mobile version)
    async def get_player_stats_api_mobile(self, player_name, lang):
        # Player level, played hours, etc
        player_id = self.get_player_id(player_name)
        if player_id == -1:
            embed = discord.Embed(
                title=self.lang_dict["general_error2"][lang].format(player_name),
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
        except PlayerNotFound:
            embed = discord.Embed(
                description=self.lang_dict["general_error2"][lang].format(player_name),
                colour=discord.colour.Color.red()
            )
            return [embed]

        # Overall Info
        ss = self.lang_dict["stats_s1"][lang + "_mobile"]
        total = int(info.wins) + int(info.losses)
        wr = await self.calc_win_rate(int(info.wins), total)
        ss = ss.format(str(info.playerName), str(info.accountLevel), wr, str(total), str(info.leaves))

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
        s2 = self.lang_dict["stats_s2"][lang + "_mobile"]

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
        s3 = self.lang_dict["stats_s3"][lang + "_mobile"]
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
            match_data = self.lang_dict["general_error2"][lang].format(player_name)
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
            match_data = self.lang_dict["general_error2"][lang].format(player_name)
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
            match_data = self.lang_dict["general_error"][lang].format(player_name)
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

                ss = self.lang_dict["stats_champ"][lang].replace("*", " ")

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
            match_data = self.lang_dict["general_error2"][lang].format(player_name)
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
            match_data = self.lang_dict["general_error2"][lang].format(player_name)
            embed = discord.Embed(
                description=match_data,
                colour=discord.colour.Color.dark_teal()
            )
            return [embed]
        if stats is None:  # Private account
            match_data = self.lang_dict["general_error"][lang].format(player_name)
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

                ss = self.lang_dict["stats_champ"][lang]

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

    async def auto_update(self, discord_id):
        player_name = await self.check_player_name(discord_id)
        if player_name == "None":
            return None
        player_id = self.get_player_id(player_name)
        if player_id == -1:
            return None
        try:
            paladins_data = self.bot.paladinsAPI.getMatchHistory(player_id)
            # Endpoint down
            if paladins_data is None:
                return None
        except NotFound:
            return None

        # pass the data to the update function
        await self.update(paladins_data, discord_id)

    # Helper function to track changes
    async def update(self, paladins_data, discord_id):
        directory = "user_data" + "/" + discord_id

        try:
            with open(directory) as json_f:
                all_data = json.load(json_f)
        except FileNotFoundError:
            return None

        # update when the data was last updated
        today = datetime.now().replace(microsecond=0)
        # print(today, type(today))
        last_tracked = datetime.strptime(all_data["last_updated"], "%Y-%m-%d %H:%M:%S")
        # print(last_tracked, type(last_tracked))
        last_tracked = (today - last_tracked).seconds
        # print(last_tracked)

        all_data["last_updated"] = str(datetime.now().replace(microsecond=0))

        for match in paladins_data:
            # Check to see if this player does have match history
            if match.playerName is None:
                return None

            date_key = str(match.matchTime.split()[0])

            # Seeing if this date is already here, if not then make an empty dict.
            if date_key not in all_data["player_data"]:
                all_data["player_data"][date_key] = {}
            # print(match.matchMinutes)
            map_name = await self.convert_match_type(match.mapName)
            if "Bot Match" not in map_name:
                match_data = [match.godName, match.winStatus, match.matchMinutes, map_name,
                              match.kills, match.deaths, match.assists, match.damage, match.healing,
                              match.damageMitigated, match.damageTaken, match.credits, match.healingPlayerSelf,
                              match.matchQueueId]

                # Seeing if a match id has been recorded
                if str(match.matchId) not in all_data["player_data"][date_key]:
                    all_data["player_data"][date_key][str(match.matchId)] = match_data

        # Save changes to the file
        with open(directory, 'w') as json_f:
            json.dump(all_data, json_f)

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

    @commands.command(name='top', pass_context=True, ignore_extra=False, aliases=["Top", "bottom", "Bottom"])
    @commands.cooldown(3, 30, commands.BucketType.user)
    # Gets stats for a champ using Paladins API
    async def top(self, ctx, player_name, option, amount="limit"):
        # lang = await self.bot.check_language(ctx=ctx)
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
            match_data = self.lang_dict["general_error2"][lang].format(player_name)
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
            match_data = self.lang_dict["general_error"][lang].format(player_name)
            embed = discord.Embed(
                description=match_data,
                colour=discord.colour.Color.dark_teal()
            )
            return embed
        if stats is None:  # Private account
            match_data = self.lang_dict["general_error"][lang].format(player_name)
            embed = discord.Embed(
                description=match_data,
                colour=discord.colour.Color.dark_teal()
            )
            return embed

        player_champion_data = []
        count = 0

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

        # amount converting
        limit = -1 if amount == "all" else 10

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
        message = "{:15}    {:7} {:6} {:10} {:9} {:6}\n{}\n" \
            .format("Champion", "Level", "KDA", "Win Rate", "Matches", "Time(mins.)",
                    "------------------------------------------------------------------")
        message2 = ""

        for i, champ in enumerate(player_champion_data, start=0):
            if i == limit:
                break
            champ = [str(j) for j in champ]  # convert all elements to string to make formatting easier
            hours = int(int(champ[5]) / 60)
            minutes = int(champ[5]) % 60
            champ[5] = "{}h {}m".format(hours, minutes)
            if i >= 9:
                if i < 20:
                    message += "{}. {:15}{:7} {:6} {:10} {:9} {:6}\n".format(i + 1, *champ)
                else:
                    message2 += "{}. {:15}{:7} {:6} {:10} {:9} {:6}\n".format(i + 1, *champ)
            else:
                message += "{}.  {:15}{:7} {:6} {:10} {:9} {:6}\n".format(i + 1, *champ)

        await ctx.send("```md\n" + message + "```")
        if message2 != "":
            await ctx.send("```md\n" + message2 + "```")

    @commands.command(name='deck', pass_context=True, aliases=["Deck", "decks", "Decks", "talia", "Talia"],
                      ignore_extra=False)
    @commands.cooldown(4, 30, commands.BucketType.user)
    async def deck(self, ctx, player_name, champ_name, deck_index=None):
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

        await helper.store_commands(ctx.author.id, "deck")
        async with ctx.channel.typing():
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

            champ_name = await self.convert_champion_name(champ_name)

            player_decks = self.bot.paladinsAPI.getPlayerLoadouts(player_id)
            if (len(player_decks)) <= 1 and player_decks[0].deckId == 0:
                await ctx.send("`Can't get decks for {} because their account is private.`\n"
                               "<:ying_mad:576792455148601345><:lian_palm:576792454968246282>".format(player_name))
                return None

            deck_list = []

            deck = None
            found = False
            index = 0
            for decks in player_decks:
                if decks.godName == champ_name:
                    index += 1
                    try:
                        if deck_index is not None and index == int(deck_index):
                            deck = decks
                            found = True
                        else:
                            deck_list.append(decks.deckName)
                    except ValueError:
                        await ctx.send("Please enter the <deck_index> as a number of deck you want.\n\n" +
                                       "Example: `>>deck {} {} {}`".format(player_name, champ_name, "1"))
                        return None

            # Correcting player name
            for decks in player_decks:
                # print(decks.playerName)  # ToDo Console player name missing
                if decks.playerName == "":
                    player_name = str(decks.playerId)
                else:
                    player_name = decks.playerName
                break

            if deck_index is None or found is False:
                message = "Decks for " + player_name + "'s " + champ_name + ":\n" + self.dashes + "\n"
                for i, deck in enumerate(deck_list, start=1):
                    message += str(i) + '. ' + deck + "\n"

                await ctx.send("```md\n" + message + "```")
            else:
                buffer = await helper.create_deck_image(player_name, champ_name, deck)
                file = discord.File(filename="Deck.png", fp=buffer)
                await ctx.send("```Enjoy the beautiful image below.```", file=file)

    @commands.command(name='history', pass_context=True, ignore_extra=False,
                      aliases=["History", "historia", "Historia"])
    @commands.cooldown(3, 40, commands.BucketType.user)
    async def history(self, ctx, player_name, amount=None, champ_name=None):
        lang = await self.bot.language.check_language(ctx=ctx)
        # Maybe convert the player name
        personal_update = False
        if str(player_name) == "me":
            personal_update = True
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
            except NotFound:
                await ctx.send("Player does not have recent match data or their account is private. Make sure the first"
                               " parameter is a player name and not the Match Id.")
                return None

            # Update player history
            if personal_update:
                await self.update(paladins_data, str(ctx.author.id))

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
                        class_index = self.get_champ_class(match.godName)
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

    # Returns an image of a match with player details
    @commands.command(name='match', pass_context=True, ignore_extra=False, aliases=["Match", "mecz", "Mecz"])
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def match(self, ctx, player_name, match_id=None, colored="-b"):
        lang = await self.bot.language.check_language(ctx=ctx)
        # Maybe convert the player name
        personal_update = False
        if str(player_name) == "me":
            personal_update = True
            player_name = await self.check_player_name(str(ctx.author.id))
        elif player_name[0] == "<" and player_name[1] == "@":  # 99% that someone has been mentioned
            player_name = player_name.replace("<", "").replace(">", "").replace("@", "").replace("!", "")
            if len(player_name) == 18:
                player_name = await self.check_player_name(player_name)

        if player_name == "None":
            await ctx.send("You have not stored your IGN yet. To do so please use the store command like so: "
                           "`>>store Paladins_IGN`")
            return None

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

        await helper.store_commands(ctx.author.id, "match")
        async with ctx.channel.typing():
            try:
                paladins_data = self.bot.paladinsAPI.getMatchHistory(player_id)
                # Endpoint down
                if paladins_data is None:
                    await ctx.send("```fix\nPaladins Endpoint down (no data returned). Please try again later and "
                                   "hopefully by then Evil Mojo will have it working again.```")
                    return None
            except NotFound:
                await ctx.send("Player does not have recent match data or their account is private. Make sure the first"
                               " parameter is a player name and not the Match Id.")
                return None

            # Update player history
            if personal_update:
                await self.update(paladins_data, str(ctx.author.id))

            for match in paladins_data:
                # Check to see if this player does have match history
                if match.playerName is None:
                    await ctx.send("Player does not have recent match data or their account is private.")
                    return None

                team1_data = []
                team2_data = []
                team1_champs = []
                team2_champs = []
                team1_parties = {}
                team2_parties = {}
                temp = []
                new_party_id = 0

                # handles if they provide the color option and no match id
                try:
                    match_id = int(match_id)
                except BaseException:
                    colored = match_id
                    match_id = -1

                if match_id == -1 or match_id == match.matchId:
                    match_data = self.bot.paladinsAPI.getMatch(match.matchId)
                    match_info = [match.winStatus, match.matchMinutes, match.matchRegion,
                                  str(match.mapName).replace("LIVE", ""), match.team1Score, match.team2Score]
                    # print(match.winStatus, match.matchMinutes, match.matchRegion,
                    #      str(match.mapName).replace("LIVE", ""))
                    for pd in match_data:
                        temp = [pd.banName1, pd.banName2, pd.banName3, pd.banName4]
                        if pd.taskForce == 1:
                            kda = "{}/{}/{}".format(pd.killsPlayer, pd.deaths, pd.assists)
                            team1_data.append([pd.playerName, pd.accountLevel, "{:,}".format(pd.goldEarned), kda,
                                               "{:,}".format(pd.damagePlayer), "{:,}".format(pd.damageTaken),
                                               pd.objectiveAssists, "{:,}".format(pd.damageMitigated),
                                               "{:,}".format(pd.healing), pd.partyId, pd.platform])
                            team1_champs.append(pd.referenceName)
                            if pd.partyId not in team1_parties or pd.partyId == 0:
                                team1_parties[pd.partyId] = ""
                            else:
                                if team1_parties[pd.partyId] == "":
                                    new_party_id += 1
                                    team1_parties[pd.partyId] = "" + str(new_party_id)
                        else:
                            kda = "{}/{}/{}".format(pd.killsPlayer, pd.deaths, pd.assists)
                            team2_data.append([pd.playerName, pd.accountLevel, "{:,}".format(pd.goldEarned), kda,
                                               "{:,}".format(pd.damagePlayer), "{:,}".format(pd.damageTaken),
                                               pd.objectiveAssists, "{:,}".format(pd.damageMitigated),
                                               "{:,}".format(pd.healing), pd.partyId, pd.platform])
                            team2_champs.append(pd.referenceName)
                            if pd.partyId not in team2_parties or pd.partyId == 0:
                                team2_parties[pd.partyId] = ""
                            else:
                                if team2_parties[pd.partyId] == "":
                                    new_party_id += 1
                                    team2_parties[pd.partyId] = str(new_party_id)

                    # print("team1: " + str(team1_parties), "team2: " + str(team2_parties))
                    color = True if colored == "-c" else False

                    buffer = await helper.create_history_image(team1_champs, team2_champs, team1_data, team2_data,
                                                               team1_parties, team2_parties, (match_info + temp), color)

                    file = discord.File(filename="TeamMatch.png", fp=buffer)

                    await ctx.send("```You are an amazing person!```", file=file)
                    return None

            # If the match id could not be found
            embed = discord.Embed(
                description="Could not find a match with the match id: " + str(match_id),
                colour=discord.colour.Color.dark_teal()
            )

            # If player has not played recently
            if match_id == -1:
                embed.description = "Player does not have recent match data."

            await ctx.send(embed=embed)

    # Returns simple match history details
    @commands.command(name='last', pass_context=True, ignore_extra=False, aliases=["Last", "ostatni", "Ostatni"])
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def last(self, ctx, player_name, match_id=-1):
        lang = await self.bot.language.check_language(ctx=ctx)
        # Maybe convert the player name
        personal_update = False
        if str(player_name) == "me":
            personal_update = True
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
        except NotFound:
            await ctx.send("Player does not have recent match data or their account is private. Make sure the first"
                           " parameter is a player name and not the Match Id.")
            return None

        # Update player history
        if personal_update:
            await self.update(paladins_data, str(ctx.author.id))

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

                try:
                    embed.set_thumbnail(url=await helper.get_champ_image(match.godName))
                except BaseException:
                    print("oops")

                map_name = match.mapName.replace("LIVE ", "").replace("Ranked ", "").replace(" (TDM)", "") \
                    .replace(" (Onslaught) ", "").replace(" (Siege)", "").replace("Practice ", "").lower() \
                    .replace(" ", "_").replace("'", "")
                map_url = "https://raw.githubusercontent.com/EthanHicks1/PaladinsAssistantBot/master/icons/maps/{}.png"\
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

    # Gets details about a player in a current match using the Paladins API
    # Get stats for a player's current match.
    @commands.command(name='current', pass_context=True, aliases=["Current", "partida", "Partida", "obecny", "Obecny"],
                      ignore_extra=False)
    @commands.cooldown(30, 30, commands.BucketType.user)
    async def current(self, ctx, player_name, option="-s"):
        print(Fore.MAGENTA + f'{round(Process(getpid()).memory_info().rss/1024/1024, 2)} MB')
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

        value = -1
        if option == "-a":
            value = 1
        can_use = await helper.store_commands(ctx.author.id, "current", value)
        async with ctx.channel.typing():
            # Data Format
            # {'Match': 795950194, 'match_queue_id': 452, 'personal_status_message': 0, 'ret_msg': 0, 'status': 3,
            # 'status_string': 'In Game'}

            # Gets player id and error checks
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
            data = self.bot.paladinsAPI.getPlayerStatus(player_id)

            # Private account if it makes it this far in the code
            if data.status == 5:
                await ctx.send("`Can't get the current match for {} because their account is private.`\n"
                               "<:ying_mad:576792455148601345><:lian_palm:576792454968246282>".format(player_name))
                return None

            if data == 0:
                await ctx.send(str("Player " + player_name + " is not found."))
                return None
            if data.status == 0:
                await ctx.send("Player is offline.")
                return None
            elif data.status == 1:
                await ctx.send("Player is in lobby.")
                return None
            elif data.status == 2:
                await ctx.send("Player in champion selection.")
                return None

            # match_queue_id = 424 = Siege
            # match_queue_id = 445 = Test Maps (NoneType) --> no json data
            # match_queue_id = 452 = Onslaught
            # match_queue_id = 469 = DTM
            # match_queue_id = 486 = Ranked (Invalid)

            current_match_queue_id = data.queueId

            match_string = "Unknown match Type"
            if current_match_queue_id == 424:
                match_string = "Siege"
            elif current_match_queue_id == 445:
                await ctx.send("No data for Test Maps.")
                return None
            elif current_match_queue_id == 452:
                match_string = "Onslaught"
            elif current_match_queue_id == 469:
                match_string = "Team Death Match"
            elif current_match_queue_id == 486:
                match_string = "Ranked"
            elif current_match_queue_id == 428:
                match_string = "Ranked Console"

            # Data Format
            # {'Account_Level': 17, 'ChampionId': 2493, 'ChampionName': 'Koga', 'Mastery_Level': 10, 'Match': 795511902,
            # 'Queue': '424', 'SkinId': 0, 'Tier': 0, 'playerCreated': '11/10/2017 10:00:03 PM', 'playerId': '12368291',
            # 'playerName': 'NabbitOW', 'ret_msg': None, 'taskForce': 1, 'tierLosses': 0, 'tierWins': 0}
            try:
                players = self.bot.paladinsAPI.getMatch(data.matchId, True)
            except BaseException:
                await ctx.send("Please makes sure you use the current command on Siege, Ranked, Team Death Match, "
                               "or Ranked. Other match queues are not fully supported by Hi-Rez for getting stats.")
                # + str(e))
                return None
            # print(players)
            team1 = []
            team1_ranks = []
            team1_champs = []
            team1_overall = [0, 0, 0, 0]  # num, level, win rate, kda
            team1_embed = []
            mobile_data1 = []

            team2 = []
            team2_ranks = []
            team2_champs = []
            team2_overall = [0, 0, 0, 0]  # num, level, win rate, kda
            team2_embed = []
            mobile_data2 = []

            for player in players:
                try:
                    name = int(player.playerId)
                    # console player's number
                    if str(player.playerId) == str(player_name):
                        player_name = player.playerName
                except TypeError:
                    print("***Player ID error: " + str(type(player.playerId)))
                    name = "-1"
                except BaseException as e:
                    print("***Player ID error: " + str(type(player.playerId)) + "Error: " + str(e))
                    name = "-1"
                if int(player.taskForce) == 1:
                    team1.append(name)
                    team1_champs.append(player.godName)
                    if current_match_queue_id == 486 or current_match_queue_id == 428:
                        team1_ranks.append(str(player.tier))
                else:
                    team2.append(name)
                    team2_champs.append(player.godName)
                    if current_match_queue_id == 486 or current_match_queue_id == 428:
                        team2_ranks.append(str(player.tier))

            # Checking for is_on_mobile() status
            mobile_status = False
            if ctx.guild is None:  # In DM's
                guilds = self.bot.guilds
                for guild in guilds:
                    member = guild.get_member(ctx.author.id)
                    if member is not None:
                        mobile_status = member.is_on_mobile()
            else:
                mobile_status = ctx.author.is_on_mobile()

            match_data = ""
            match_data += player_name + " is in a " + match_string + " match."  # Match Type
            match_info_embed = match_data
            match_data += str('\n\n{:18}  {:7}  {:8}  {:6}\n\n').format("Player name", "Level", "Win Rate", "KDA")
            player_champ_data = str('\n\n{:18}  {:7}  {:8}  {:6}\n\n').format("Champion name", "Level",
                                                                              "Win Rate", "KDA")
            # Slow version in case Hi-Rez slows down access to API again
            # """
            data1 = []
            data2 = []
            # start = time.time()
            for player in team1:
                d1 = await self.get_global_kda(player)
                data1.append(d1)

            for player in team2:
                d2 = await self.get_global_kda(player)
                data2.append(d2)
            # end = time.time()
            # print(end - start)
            # """

            """
            # start = time.time()
            # Create a list of tasks to run in parallel
            tasks = []
            tasks2 = []
            for player in team1:
                tasks.append(self.get_global_kda(player))

            for player in team2:
                tasks2.append(self.get_global_kda(player))

            data1 = await asyncio.gather(*tasks)
            data2 = await asyncio.gather(*tasks2)
            """

            # end = time.time()
            # print(end - start)

            # Add in image creation task
            buffer = await helper.create_match_image(team1_champs, team2_champs, team1_ranks, team2_ranks)

            for pl, champ in zip(data1, team1_champs):
                if not mobile_status:
                    ss = str('*{:18} Lv. {:3}  {:8}  {:6}\n')
                    ss = ss.format(pl[0], str(pl[1]), pl[2], pl[3])
                    """This Block of code adds color based on Win Rate"""
                    if "???" in pl[2]:
                        pass
                    elif (float(pl[2].replace(" %", ""))) > 55.00:
                        ss = ss.replace("*", "+")
                    elif (float(pl[2].replace(" %", ""))) < 49.00:
                        ss = ss.replace("*", "-")
                    """^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"""
                    match_data += ss
                else:
                    p1 = "{} (Lv. {})".format(pl[0], pl[1])
                    p2 = "{}% \u200b \u200b \u200b \u200b \u200b \u200b {} KDA".format(pl[2], pl[3])
                    team1_embed.append([p1, p2])
                    """
                    embed.add_field(name="{} (Lv. {})".format(pl[0], pl[1]),
                                    value="{}% \u200b \u200b \u200b \u200b \u200b \u200b"
                                          "{} KDA".format(pl[2], pl[3]), inline=False)
                    """

                # For teams total win rate and kda
                if pl[1] != "???" and float(pl[1]) > 50:
                    team1_overall[0] += 1  # num
                    team1_overall[1] += int(pl[1])  # level
                    try:
                        team1_overall[2] += float(pl[2])  # win rate
                        team1_overall[3] += float(pl[3])  # kda
                    except ValueError:
                        pass
                # Add in champ stats
                can_use = True  # ToDo --- Change this later
                if option == "-a" and can_use:
                    if not mobile_status:
                        player_champ_data += await self.get_champ_stats_api(pl[0], champ, 1, lang=lang)
                    else:
                        pd = await self.get_champ_stats_api(pl[0], champ, 1, lang=lang, mobile=mobile_status)
                        p1 = "{} (Lv. {})".format(pd[0], pd[1])
                        p2 = "{}% \u200b \u200b \u200b \u200b \u200b \u200b {} KDA".format(pd[2], pd[3])
                        mobile_data1.append([p1, p2])

            match_data += "\n"
            player_champ_data += "\n"

            for pl, champ in zip(data2, team2_champs):
                if not mobile_status:
                    ss = str('*{:18} Lv. {:3}  {:8}  {:6}\n')
                    ss = ss.format(pl[0], str(pl[1]), pl[2], pl[3])
                    """This Block of code adds color based on Win Rate"""
                    if "???" in pl[2]:
                        pass
                    elif (float(pl[2].replace(" %", ""))) > 55.00:
                        ss = ss.replace("*", "+")
                    elif (float(pl[2].replace(" %", ""))) < 49.00:
                        ss = ss.replace("*", "-")
                    """^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"""
                    match_data += ss
                else:
                    p1 = "{} (Lv. {})".format(pl[0], pl[1])
                    p2 = "{}% \u200b \u200b \u200b \u200b \u200b \u200b {} KDA".format(pl[2], pl[3])
                    team2_embed.append([p1, p2])
                    """
                    embed2.add_field(name="{} (Lv. {})".format(pl[0], pl[1]),
                                     value="{}% \u200b \u200b \u200b \u200b \u200b \u200b"
                                          "{} KDA".format(pl[2], pl[3]), inline=False)
                    """

                # For teams total win rate and kda
                if pl[1] != "???" and float(pl[1]) > 50:
                    team2_overall[0] += 1  # num
                    team2_overall[1] += int(pl[1])  # level
                    try:
                        team2_overall[2] += float(pl[2])  # win rate
                        team2_overall[3] += float(pl[3])  # kda
                    except ValueError:
                        pass

                # Add in champ stats
                if option == "-a" and can_use:
                    if not mobile_status:
                        player_champ_data += await self.get_champ_stats_api(pl[0], champ, 1, lang=lang)
                    else:
                        pd = await self.get_champ_stats_api(pl[0], champ, 1, lang=lang, mobile=mobile_status)
                        p1 = "{} (Lv. {})".format(pd[0], pd[1])
                        p2 = "{}% \u200b \u200b \u200b \u200b \u200b \u200b {} KDA".format(pd[2], pd[3])
                        mobile_data2.append([p1, p2])

            # Adding team win rate's and kda's
            team1_wr, team2_wr = 0, 0
            team1_level, team2_level = 0, 0
            team1_kda, team2_kda = 0, 0
            if team1_overall[0] != 0:
                team1_wr = round(team1_overall[2] / team1_overall[0], 2)
                team1_level = str(int(team1_overall[1] / team1_overall[0]))
                team1_kda = str(round(team1_overall[3] / team1_overall[0], 2))
            if team2_overall[0] != 0:
                team2_wr = round(team2_overall[2] / team2_overall[0], 2)
                team2_level = str(int(team2_overall[1] / team2_overall[0]))
                team2_kda = str(round(team2_overall[3] / team2_overall[0], 2))

            if not mobile_status:
                match_data += "\n\nAverage stats\n"
                ss1 = str('*{:18} Lv. {:3}  {:8}  {:6}\n')
                ss2 = str('*{:18} Lv. {:3}  {:8}  {:6}')

                # no need to call this if one team is 0
                if team1_wr != 0 and team2_wr != 0:
                    if abs(team1_wr - team2_wr) >= 5.0:
                        if team1_wr > team2_wr:
                            ss1 = ss1.replace("*", "+")
                            ss2 = ss2.replace("*", "-")
                        else:
                            ss1 = ss1.replace("*", "-")
                            ss2 = ss2.replace("*", "+")

                if team1_overall[0] != 0:
                    ss1 = ss1.format("Team1", team1_level, str(team1_wr), team1_kda)
                    match_data += ss1
                if team2_overall[0] != 0:
                    ss2 = ss2.format("Team2", team2_level, str(team2_wr), team2_kda)
                    match_data += ss2
            else:  # mobile version
                p2 = "Lv. {} \u200b \u200b \u200b \u200b \u200b \u200b {}% " \
                     "\u200b \u200b \u200b \u200b \u200b \u200b {} KDA".format(team1_level, team1_wr, team1_kda)
                team1_embed.append(["Team one's averages: ", p2])
                """
                embed_title.add_field(name="Team one's averages: ",
                                      value="Lv. {} \u200b \u200b \u200b \u200b \u200b \u200b {}% "
                                            "\u200b \u200b \u200b \u200b \u200b \u200b {} KDA"
                                      .format(team1_level, team1_wr, team1_kda),
                                      inline=False)
                """
                p2 = "Lv. {} \u200b \u200b \u200b \u200b \u200b \u200b {}% " \
                     "\u200b \u200b \u200b \u200b \u200b \u200b {} KDA".format(team2_level, team2_wr, team2_kda)
                team2_embed.append(["Team two's averages: ", p2])
                """
                embed_title.add_field(name="Team two's averages: ",
                                      value="Lv. {} \u200b \u200b \u200b \u200b \u200b \u200b {}% "
                                            "\u200b \u200b \u200b \u200b \u200b \u200b {} KDA"
                                      .format(team2_level, team2_wr, team2_kda),
                                      inline=False)
                """

            file = discord.File(filename="Team.png", fp=buffer)

            if not mobile_status:
                await ctx.send("```diff\n" + match_data + "```", file=file)
            else:  # Mobile version
                p1, p2 = team1_embed.pop()
                embed = discord.Embed(
                    colour=discord.colour.Color.blue(),
                    title=p1,
                    description=p2
                )
                for info in team1_embed:
                    embed.add_field(name=info[0], value=info[1], inline=False)

                p1, p2 = team2_embed.pop()
                embed2 = discord.Embed(
                    colour=discord.colour.Color.red(),
                    title=p1,
                    description=p2
                )
                for info in team2_embed:
                    embed2.add_field(name=info[0], value=info[1], inline=False)

                await ctx.send('```fix\n{}```'.format(match_info_embed), embed=embed)
                await ctx.send(file=file)
                await ctx.send(embed=embed2)

            if "\n" in player_champ_data and value != -1:
                if not mobile_status:
                    await ctx.send("```diff\n" + player_champ_data + "```")
                else:
                    if mobile_data1:  # List contains data
                        mobile_embed = discord.Embed(
                            colour=discord.colour.Color.blue(),
                            title="Team 1 Champion Stats:",
                            description="\u200b"
                        )
                        for info in mobile_data1:
                            mobile_embed.add_field(name=info[0], value=info[1], inline=False)
                        await ctx.send(embed=mobile_embed)

                    if mobile_data2:  # List contains data
                        mobile_embed2 = discord.Embed(
                            colour=discord.colour.Color.red(),
                            title="Team 2 Champion Stats:",
                            description="\u200b"
                        )
                        for info in mobile_data2:
                            mobile_embed2.add_field(name=info[0], value=info[1], inline=False)
                        await ctx.send(embed=mobile_embed2)

            print(Fore.MAGENTA + f'{round(Process(getpid()).memory_info().rss/1024/1024, 2)} MB')

    # Returns simple stats based on the option they choose (champ_name, or me)
    @commands.command(name='stats', aliases=['Statystyki', 'Stats'], pass_context=True, ignore_extra=False)
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
        mobile_status = False
        if ctx.guild is None:  # In DM's
            guilds = self.bot.guilds
            for guild in guilds:
                member = guild.get_member(ctx.author.id)
                if member is not None:
                    mobile_status = member.is_on_mobile()
        else:
            mobile_status = ctx.author.is_on_mobile()

        # get basic player stats
        if option is None:
            if not mobile_status:
                result = await self.get_player_stats_api(player_name, lang=lang)
                await ctx.send("```md\n" + result + "```")
            else:
                embeds = await self.get_player_stats_api_mobile(player_name, lang=lang)
                for embed in embeds:
                    await ctx.send(embed=embed)
        # get stats for a specific character
        else:
            champ_name = await self.convert_champion_name(option)
            if not mobile_status:
                result = await self.get_champ_stats_api(player_name, champ_name, simple=0, lang=lang)
                await ctx.send(embed=result)
            # mobile version
            else:
                embeds = await self.get_champ_stats_api_mobile(player_name, champ_name, lang=lang)
                for embed in embeds:
                    await ctx.send(embed=embed)

    # Stores Player's IGN for the bot to use
    @commands.command(name='store', pass_context=True, ignore_extra=False, aliases=["zapisz", "Zapisz", "Store"])
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def store_player_name(self, ctx, player_ign):
        with open("player_discord_ids") as json_f:
            player_discord_ids = json.load(json_f)

        player_discord_ids.update({str(ctx.author.id): player_ign})  # update dict

        # need to update the file now
        print("Stored a IGN in conversion dictionary: " + player_ign)
        with open("player_discord_ids", 'w') as json_f:
            json.dump(player_discord_ids, json_f)
        await ctx.send("Your Paladins In-Game-name is now stored as `" + player_ign +
                       "`. You can now use the keyword `me` instead of typing out your name")

    @commands.is_owner()
    @commands.command()
    async def testing(self, ctx):
        """
        start = time.time()
        # team1 = ["Ash", "Makoa", "Willo", "Seris"]

        team1 = ["Ash", "Makoa", "Willo", "Seris", "Io"]
        buffer = await helper.create_team_image(team1, [])
        file = discord.File(filename="Team.png", fp=buffer)
        await ctx.send("```diff\n" + "bruh" + "```", file=file)
        end = time.time()
        print(end - start)
        """

        # info = await self.get_player_current_stats_api("FeistyJalapeno")
        # await ctx.send(info)
        # return None

        info = ""
        for i in range(0, 20):
            td = await self.get_global_kda("FeistyJalapeno")
            info += str(td) + "\n"

        await ctx.send(info)
        """
        for i in range(0, 10):
            embed = discord.Embed(
                description="Test limit: " + str(i+1) + "\nplayer's stats. ",
                colour=discord.colour.Color.dark_teal(),
            )
            await ctx.send(embed=embed)
        """
        return None


# Add this class to the cog list
def setup(bot):
    bot.add_cog(PaladinsAPICog(bot))
