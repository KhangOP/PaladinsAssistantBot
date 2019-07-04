import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import requests
import my_utils as helper
from datetime import datetime; datetime.now
from datetime import date

from pyrez.api import PaladinsAPI
from pyrez.exceptions import PlayerNotFound
from pyrez.exceptions import NotFound
import json
import aiohttp
import asyncio
import time
from psutil import Process
from os import getpid

from colorama import Fore

file_name = "token"
# Gets ID and KEY from a file
with open(file_name, 'r') as f:
    TOKEN = f.readline().strip()    # Does nothing
    PREFIX = f.readline()           # Does nothing
    ID = int(f.readline())
    KEY = f.readline()
f.close()


def session_created(session):
    print("New sessionID: {}".format(session))
    print("Timestamp: {}".format(datetime.now()))


paladinsAPI = PaladinsAPI(devId=ID, authKey=KEY)
paladinsAPI.onSessionCreated += session_created


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
    SUPPORTS = ["Grohk", "Grover", "Ying", "Mal Damba", "Seris", "Jenos", "Furia", "Pip"]

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
    def color_win_rates(cls, text, win_rate):
        if float(win_rate) > 60.0:
            return "+" + text
        elif float(win_rate) < 50.0 and float(win_rate) != 0.0:
            return "-" + text
        else:
            return "*" + text

    # Get the player id for a player based on their name. First it checks a dictionary and if they are not in there then
    # it does an API call to get the player's id. Then it writes that id to the dictionary. Helps save API calls.
    @staticmethod
    def get_player_id(player_name):
        if str(player_name).isnumeric():
            return player_name
        with open("player_ids") as json_f:
            player_ids = json.load(json_f)

        # This player is already in the dictionary and therefor we don't need to waste an api call to get the player id.
        if player_name in player_ids:
            return player_ids[player_name]
        else:
            try:
                player = paladinsAPI.getPlayer(player_name)
            except BaseException:
                return -1  # invalid name
            new_id = player.playerId
            player_ids[player_name] = new_id  # store the new id in the dictionary

            # need to update the file now
            print("Added a new player the dictionary: " + player_name)
            with open("player_ids", 'w') as json_f:
                json.dump(player_ids, json_f)
            return new_id

    @classmethod
    def check_player_name(cls, player_discord_id):
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
        if assists == 0:  # Could happen
            assists = 1
        if deaths == 0:  # Prefect KDA
            return str(kills + (assists / 2))
        return str('{0:.2f}'.format(float(kills + (assists / 2)) / deaths))

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

    @classmethod
    # Helper function to the get_player_elo(player_name) function
    async def return_mode(cls, name):
        mode = ""
        if name == "Siege":
            mode += "Siege rating: \n"
        elif name == "Survival":
            mode += "Onslaught rating: \n"  # Rename to onslaught
        elif name == "Deathmatch":
            mode += "Team Deathmatch rating: \n"
        else:
            mode += "Overall Guru Score: \n"
        return mode

    # Gets KDA and Win Rate for a player from Guru
    @classmethod
    async def get_global_kda(cls, player_id):
        url = "http://nonsocial.herokuapp.com/api/kda?player=" + str(player_id)
        async with aiohttp.ClientSession(conn_timeout=5, read_timeout=5) as cs:
            async with cs.get(url) as r:
                soup = await r.text()  # returns dict

                # Error checking to make sure that the player was found on the site
                if 'ERROR' in soup:
                    error = ["Private Account", "???", "???", "???"]
                    return error

                split1 = soup.split("(Level ")

                try:
                    player_name = str(split1[0]).strip()  # Player Name
                except BaseException:
                    print(Fore.RED + str(soup))
                    return ["Connection Error", "???", "???", "???"]
                level = split1[1].split(")")[0]  # Level
                kda = soup.split("- ")[1].split(" KDA")[0]  # KDA
                win_rate = soup.split("Win rate: ")[1].split("%")[0]  # Win Rate

                stats = [player_name, level, win_rate, kda]

                return stats

    # Uses Paladins API to get overall stats for a player
    async def get_player_stats_api(self, player_name, lang):
        # Player level, played hours, etc
        player_id = self.get_player_id(player_name)
        if player_id == -1:
            return self.lang_dict["general_error2"][lang].format(player_name)
        try:
            info = paladinsAPI.getPlayer(player_id)
        except PlayerNotFound:
            return self.lang_dict["general_error2"][lang].format(player_name)

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
        ss += s3.format(self.dashes, str(info.createdDatetime).split()[0], str(info.lastLoginDatetime).split()[0],
                        str(info.platform), str(info.playedGods), str(info.totalAchievements))
        return ss

    # Uses Paladins API to get overall stats for a player (Mobile version)
    async def get_player_stats_api_mobile(self, player_name, lang):
        # Player level, played hours, etc
        player_id = self.get_player_id(player_name)
        if player_id == -1:
            return self.lang_dict["general_error2"][lang].format(player_name)
        try:
            info = paladinsAPI.getPlayer(player_id)
        except PlayerNotFound:
            return self.lang_dict["general_error2"][lang].format(player_name)

        embed = discord.Embed(
            title="`Casual stats:`",
            colour=discord.colour.Color.dark_teal(),
        )

        total = int(info.wins) + int(info.losses)
        wr = await self.calc_win_rate(int(info.wins), total)
        # embed.add_field(name='Casual stats:', value="```-----```", inline=False)
        embed.add_field(name='Name:', value=info.playerName, inline=False)
        embed.add_field(name='Account Level:', value=info.accountLevel, inline=False)
        embed.add_field(name='Win Rate:', value="{}% out of {} matches".format(wr, total), inline=False)
        embed.add_field(name='Times Deserted:', value=str(info.leaves), inline=False)

        # Get the platform's ranked stats
        platform = str(info.platform).lower()
        if platform == "steam" or platform == "hirez":
            ranked = info.rankedKeyboard
        else:
            ranked = info.rankedController

        win = int(ranked.wins)
        lose = int(ranked.losses)
        wr = await self.calc_win_rate(win, win + lose)

        embed2 = discord.Embed(
            title="`Ranked stats for Season {}:`".format(ranked.currentSeason),
            colour=discord.colour.Color.dark_magenta(),
        )
        # embed2.add_field(name='Ranked stats for Season {}:'.format(ranked.currentSeason), value="```-----```",
        #                 inline=False)
        embed2.add_field(name='Rank:', value=ranked.currentRank.getName(), inline=False)
        embed2.add_field(name='TP:', value="{} (position: {})".format(ranked.currentTrumpPoints,
                                                                      ranked.leaderboardIndex), inline=False)
        embed2.add_field(name='Win Rate:', value="{}% ({}-{})".format(wr, win, lose), inline=False)
        embed2.add_field(name='Times Deserted:', value=str(ranked.leaves), inline=False)

        embed3 = discord.Embed(
            title="`Extra details:`",
            colour=discord.colour.Color.dark_teal(),
        )
        # embed3.add_field(name='Extra details:', value="```-----```", inline=False)
        embed3.add_field(name='Account created on:', value=str(info.createdDatetime).split()[0], inline=False)
        embed3.add_field(name='Last login on:', value=str(info.lastLoginDatetime).split()[0], inline=False)
        embed3.add_field(name='Platform:', value=str(info.platform), inline=False)
        embed3.add_field(name='MasteryLevel:', value=str(info.playedGods), inline=False)
        embed3.add_field(name='Steam Achievements completed:', value="{}/{}".format(info.totalAchievements, 58),
                         inline=False)

        embeds = [embed, embed2, embed3]
        return embeds

    @classmethod
    # Gets elo's for a player from the Paladins Guru site?
    async def get_player_elo(cls, player_name):
        url = "http://paladins.guru/profile/pc/" + str(player_name) + "/casual"
        soup = BeautifulSoup(requests.get(url, headers={'Connection': 'close'}).text, 'html.parser')
        soup = str(soup.get_text()).split(" ")
        data = list(filter(None, soup))

        stats = ""
        mode = ""

        # Gets elo information below
        for i, row in enumerate(data):
            if data[i] == "Siege" or data[i] == "Survival" or data[i] == "Deathmatch" or data[i] == "Score":
                if data[i + 1] == "Rank":
                    mode = await cls.return_mode(data[i])
                    mode += str("Rank: " + data[i + 2])  # Rank
                    mode += str(" (Top " + data[i + 5] + ")\n")  # Rank %
                    mode += str("Elo: " + data[i + 6] + "\n")  # Elo
                    mode += str("Win Rate: " + data[i + 8])  # Win Rate
                    mode += str(" (" + data[i + 10] + "-")  # Wins
                    mode += data[i + 11] + ")"  # Loses
                    stats += mode + "\n\n"
                elif data[i + 1] == "-":
                    mode = await cls.return_mode(data[i])
                    mode += str("Rank: ???")  # Rank
                    mode += str(" (Top " + "???" + ")\n")  # Rank %
                    mode += str("Elo: " + data[i + 2] + "\n")  # Elo
                    mode += str("Win Rate: " + data[i + 4])  # Win Rate
                    mode += str(" (" + data[i + 6] + "-")  # Wins
                    mode += data[i + 7] + ")"  # Loses
                    stats += mode + "\n\n"
            if data[i] == "Siege":
                if data[i + 1] == "Normal:":
                    break

        # Checking if the player has any data for this season
        if mode == "":
            return "The player: " + player_name + " does not have any matches this season."

        return stats

    # Gets stats for a champ using Paladins API
    async def get_champ_stats_api(self, player_name, champ, simple, lang):
        # Gets player id and error checks
        player_id = self.get_player_id(player_name)
        if player_id == -1:
            if simple == 1:
                ss = str('*{:18} Lv. {:3}  {:7}   {:6}\n')
                ss = ss.format(champ, "???", "???", "???")
                return ss
            match_data = self.lang_dict["general_error2"][lang].format(player_name)
            embed = discord.Embed(
                description=match_data,
                colour=discord.colour.Color.dark_teal()
            )
            return embed
        try:
            stats = paladinsAPI.getChampionRanks(player_id)  # Todo Console name not returned in data (but correct)
            # {"Assists": 2771, "Deaths": 2058, "Gold": 880190, "Kills": 2444, "LastPlayed": "6/14/2019 9:49:51 PM",
            # "Losses": 125, "MinionKills": 253, "Minutes": 3527, "Rank": 58, "Wins": 144, "Worshippers": 33582898,
            # "champion": "Makoa", "champion_id": "2288", "player_id": "704972387", "ret_msg": null}
        except BaseException:
            ss = str('*   {:15} Lv. {:3}  {:7}   {:6}\n')
            ss = ss.format(champ, "???", "???", "???")
            return ss
        if stats is None:  # Private account
            if simple == 1:
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
        count = 0

        for stat in stats:
            count += 1
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
                if simple == 1:
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
            t_wins += wins
            t_loses += losses
            if wins + losses > 20:  # Player needs to have over 20 matches with a champ for it to affect kda
                t_kda += float(kda) * (wins + losses)  # These two lines allow the kda to be weighted
                count += 1 + (wins + losses)  # aka the more a champ is played the more it affects global kda

        # They have not played this champion yet
        if ss == "":
            ss = "No data for champion: " + champ + "\n"
            if simple == 1:
                ss = str('*{:18} Lv. {:3}  {:7}   {:6}\n')
                ss = ss.format(champ, "???", "???", "???")
                return ss

        # Global win rate and kda
        global_ss = str("\n\nGlobal KDA: {}\nGlobal Win Rate: {}% ({}-{})")
        win_rate = await self.calc_win_rate(t_wins, t_wins + t_loses)
        t_kda = str('{0:.2f}').format(t_kda / count)
        global_ss = global_ss.format(t_kda, win_rate, t_wins, t_loses)
        ss += global_ss

        # Create an embed
        embed = discord.Embed(
            colour=discord.colour.Color.dark_teal()
        )
        embed.add_field(name=player_name + "'s stats: ", value='`' + ss + '`', inline=False)
        embed.set_thumbnail(url=await helper.get_champ_image(champ))
        return embed

    @classmethod
    async def do_nothing(cls):
        return -1

    '''Commands below ############################################################'''
    @commands.command(name='console', pass_context=True, ignore_extra=False)
    @commands.cooldown(6, 30, commands.BucketType.user)
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
                await ctx.send("```md\nInvalid platform name. Valid platform names are:\n1. Xbox\n2. PS4\n3. Switch```")
                return None

            # players = paladinsAPI.getPlayerId(player_name, "steam")
            # players = paladinsAPI.getPlayerId(player_name, platform)

            players = paladinsAPI.searchPlayers(player_name)

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
                player = paladinsAPI.getPlayer(player=player.playerId)

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

    @commands.command(name='top', pass_context=True, ignore_extra=False)
    @commands.cooldown(2, 30, commands.BucketType.user)
    # Gets stats for a champ using Paladins API
    async def top(self, ctx, player_name, option, order="False"):
        lang = await helper.Lang.check_language(ctx=ctx)
        # Maybe convert the player name
        if str(player_name) == "me":
            player_name = self.check_player_name(str(ctx.author.id))
        elif player_name[0] == "<" and player_name[1] == "@":  # 99% that someone has been mentioned
            player_name = player_name.replace("<", "").replace(">", "").replace("@", "").replace("!", "")
            if len(player_name) == 18:
                player_name = self.check_player_name(player_name)

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
                description=match_data,
                colour=discord.colour.Color.dark_teal()
            )
            return embed
        try:
            stats = paladinsAPI.getChampionRanks(player_id)
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
            if not last_played:  # Bought the champ but never played them
                break

            player_champion_data.append([stat.godName, level, kda, win_rate, wins + losses, stat.json['Minutes']])

        # Convert option
        ordering = False if order == "low" else True

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
        message = "{:15}    {:7} {:6} {:10} {:9} {:6}\n{}\n"\
            .format("Champion", "Level", "KDA", "Win Rate", "Matches", "Time(mins.)",
                    "------------------------------------------------------------------")

        for i, champ in enumerate(player_champion_data, start=0):
            if i == 10:
                break
            champ = [str(j) for j in champ]  # convert all elements to string to make formatting easier
            hours = int(int(champ[5]) / 60)
            minutes = int(champ[5]) % 60
            champ[5] = "{}h {}m".format(hours, minutes)
            if i == 9:
                message += "{}. {:15}{:7} {:6} {:10} {:9} {:6}\n".format(i + 1, *champ)
            else:
                message += "{}.  {:15}{:7} {:6} {:10} {:9} {:6}\n".format(i + 1, *champ)

        await ctx.send("```md\n" + message + "```")

    @commands.command(name='deck', pass_context=True, aliases=["decks", "talia"], ignore_extra=False)
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def deck(self, ctx, player_name, champ_name, deck_index=None):
        lang = await helper.Lang.check_language(ctx=ctx)
        # Maybe convert the player name
        if str(player_name) == "me":
            player_name = self.check_player_name(str(ctx.author.id))
        elif player_name[0] == "<" and player_name[1] == "@":  # 99% that someone has been mentioned
            player_name = player_name.replace("<", "").replace(">", "").replace("@", "").replace("!", "")
            if len(player_name) == 18:
                player_name = self.check_player_name(player_name)

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
                    description=match_data,
                    colour=discord.colour.Color.dark_teal()
                )
                await ctx.send(embed=embed)
                return None

            champ_name = await self.convert_champion_name(champ_name)

            player_decks = paladinsAPI.getPlayerLoadouts(player_id)
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

    @commands.command(name='history', pass_context=True, ignore_extra=False, aliases=["historia"])
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def history(self, ctx, player_name, amount=10, champ_name=None):
        lang = await helper.Lang.check_language(ctx=ctx)
        # Maybe convert the player name
        if str(player_name) == "me":
            player_name = self.check_player_name(str(ctx.author.id))
        elif player_name[0] == "<" and player_name[1] == "@":  # 99% that someone has been mentioned
            player_name = player_name.replace("<", "").replace(">", "").replace("@", "").replace("!", "")
            if len(player_name) == 18:
                player_name = self.check_player_name(player_name)

        if player_name == "None":
            await ctx.send("You have not stored your IGN yet. To do so please use the store command like so: "
                           "`>>store Paladins_IGN`")
            return None

        await helper.store_commands(ctx.author.id, "history")
        async with ctx.channel.typing():
            if amount > 50 or amount <= 1:
                await ctx.send("Please enter an amount between 2-50")
                return None
            player_id = self.get_player_id(player_name)
            if player_id == -1:
                await ctx.send(self.lang_dict["general_error2"][lang].format(player_name))
                return None
            if champ_name:  # Check in case they don't provide champ name
                champ_name = await self.convert_champion_name(champ_name)
            paladins_data = paladinsAPI.getMatchHistory(player_id)

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
                            total_kda[class_index*2] += float(kda)
                            total_kda[class_index*2+1] += 1
                            if match.winStatus == "Loss":
                                total_wins[class_index*2+1] += 1  # Losses
                            else:
                                total_wins[class_index*2] += 1    # Wins
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
            d_t = total_wins[0] + total_wins[1]     # Damage total matches
            f_t = total_wins[2] + total_wins[3]     # Flank total matches
            t_t = total_wins[4] + total_wins[5]     # Tank total matches
            s_t = total_wins[6] + total_wins[7]     # Healer total matches
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
            ss = ss.replace("Total", self.color_win_rates("Total", total_wr))\
                .replace("Damages", self.color_win_rates("Damages", d_wr))\
                .replace("Flanks", self.color_win_rates("Flanks", f_wr))\
                .replace("Tanks", self.color_win_rates("Tanks", t_wr))\
                .replace("Healers", self.color_win_rates("Healers", s_wr))

            # KDA calc
            d_kda, f_kda, t_kda, s_kda, = 0.0, 0.0, 0.0, 0.0
            if total_kda[0] != 0:
                d_kda = round(total_kda[0]/total_kda[1], 2)
            if total_kda[2] != 0:
                f_kda = round(total_kda[2]/total_kda[3], 2)
            if total_kda[4] != 0:
                t_kda = round(total_kda[4]/total_kda[5], 2)
            if total_kda[6] != 0:
                s_kda = round(total_kda[6]/total_kda[7], 2)

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
    @commands.command(name='match', pass_context=True, ignore_extra=False, aliases=["mecz"])
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def match(self, ctx, player_name, match_id=None, colored="-b"):
        lang = await helper.Lang.check_language(ctx=ctx)
        # Maybe convert the player name
        if str(player_name) == "me":
            player_name = self.check_player_name(str(ctx.author.id))
        elif player_name[0] == "<" and player_name[1] == "@":  # 99% that someone has been mentioned
            player_name = player_name.replace("<", "").replace(">", "").replace("@", "").replace("!", "")
            if len(player_name) == 18:
                player_name = self.check_player_name(player_name)

        if player_name == "None":
            await ctx.send("You have not stored your IGN yet. To do so please use the store command like so: "
                           "`>>store Paladins_IGN`")
            return None

        player_id = self.get_player_id(player_name)

        if player_id == -1:
            match_data = self.lang_dict["general_error2"][lang].format(player_name)
            embed = discord.Embed(
                description=match_data,
                colour=discord.colour.Color.dark_teal()
            )
            await ctx.send(embed=embed)
            return None

        await helper.store_commands(ctx.author.id, "match")
        async with ctx.channel.typing():
            try:
                paladins_data = paladinsAPI.getMatchHistory(player_id)
            except NotFound:
                await ctx.send("Player does not have recent match data or their account is private. Make sure the first"
                               " parameter is a player name and not the Match Id.")
                return None

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
                    match_data = paladinsAPI.getMatch(match.matchId)
                    match_info = [match.winStatus, match.matchMinutes, match.matchRegion,
                                  str(match.mapName).replace("LIVE", ""), match.team1Score, match.team2Score]
                    # print(match.winStatus, match.matchMinutes, match.matchRegion,
                    #      str(match.mapName).replace("LIVE", ""))
                    for pd in match_data:
                        temp = [pd.banName1, pd.banName2, pd.banName3, pd.banName4]
                        if pd.taskForce == 1:
                            kda = "{}/{}/{}".format(pd.killsPlayer, pd.deaths, pd.assists)
                            # account = "{}({})".format(pd.playerName, pd.accountLevel)
                            team1_data.append([pd.playerName, pd.accountLevel, "{:,}".format(pd.goldEarned), kda,
                                               "{:,}".format(pd.damagePlayer), "{:,}".format(pd.damageTaken),
                                               pd.objectiveAssists, "{:,}".format(pd.damageMitigated),
                                               "{:,}".format(pd.healing), pd.partyId])
                            team1_champs.append(pd.referenceName)
                            if pd.partyId not in team1_parties or pd.partyId == 0:
                                team1_parties[pd.partyId] = ""
                            else:
                                if team1_parties[pd.partyId] == "":
                                    new_party_id += 1
                                team1_parties[pd.partyId] = "" + str(new_party_id)
                        else:
                            kda = "{}/{}/{}".format(pd.killsPlayer, pd.deaths, pd.assists)
                            # account = "{}({})".format(pd.playerName, pd.accountLevel)
                            team2_data.append([pd.playerName, pd.accountLevel, "{:,}".format(pd.goldEarned), kda,
                                               "{:,}".format(pd.damagePlayer), "{:,}".format(pd.damageTaken),
                                               pd.objectiveAssists, "{:,}".format(pd.damageMitigated),
                                               "{:,}".format(pd.healing), pd.partyId])
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
    @commands.command(name='last', pass_context=True, ignore_extra=False, aliases=["ostatni"])
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def last(self, ctx, player_name, match_id=-1):
        lang = await helper.Lang.check_language(ctx=ctx)
        # Maybe convert the player name
        if str(player_name) == "me":
            player_name = self.check_player_name(str(ctx.author.id))
        elif player_name[0] == "<" and player_name[1] == "@":  # 99% that someone has been mentioned
            player_name = player_name.replace("<", "").replace(">", "").replace("@", "").replace("!", "")
            if len(player_name) == 18:
                player_name = self.check_player_name(player_name)

        if player_name == "None":
            await ctx.send("You have not stored your IGN yet. To do so please use the store command like so: "
                           "`>>store Paladins_IGN`")
            return None

        await helper.store_commands(ctx.author.id, "last")
        player_id = self.get_player_id(player_name)

        if player_id == -1:
            match_data = self.lang_dict["general_error2"][lang].format(player_name)
            embed = discord.Embed(
                description=match_data,
                colour=discord.colour.Color.dark_teal()
            )
            await ctx.send(embed=embed)
            return None

        try:
            paladins_data = paladinsAPI.getMatchHistory(player_id)
        except NotFound:
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

                map_name = match.mapName.replace("LIVE ", "").replace("Ranked ", "").replace(" (TDM)", "")\
                    .replace(" (Onslaught) ", "").replace(" (Siege)", "").replace("Practice ", "").lower()\
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
    @commands.command(name='current', pass_context=True, aliases=["partida", "obecny"], ignore_extra=False)
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def current(self, ctx, player_name, option="-s"):
        print(Fore.MAGENTA + f'{round(Process(getpid()).memory_info().rss/1024/1024, 2)} MB')
        lang = await helper.Lang.check_language(ctx=ctx)
        # Maybe convert the player name
        if str(player_name) == "me":
            player_name = self.check_player_name(str(ctx.author.id))
        elif player_name[0] == "<" and player_name[1] == "@":  # 99% that someone has been mentioned
            player_name = player_name.replace("<", "").replace(">", "").replace("@", "").replace("!", "")
            if len(player_name) == 18:
                player_name = self.check_player_name(player_name)

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
            data = paladinsAPI.getPlayerStatus(player_id)

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
                players = paladinsAPI.getMatch(data.matchId, True)
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

            team2 = []
            team2_ranks = []
            team2_champs = []
            team2_overall = [0, 0, 0, 0]  # num, level, win rate, kda

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

            match_data = ""
            match_data += player_name + " is in a " + match_string + " match."  # Match Type
            match_data += str('\n\n{:18}  {:7}  {:8}  {:6}\n\n').format("Player name", "Level", "Win Rate", "KDA")
            player_champ_data = str('\n\n{:18}  {:7}  {:8}  {:6}\n\n').format("Champion name", "Level",
                                                                              "Win Rate", "KDA")

            # Create a list of tasks to run in parallel
            # Create a list of tasks to run in parallel
            tasks = []
            for player in team1:
                tasks.append(self.get_global_kda(player))

            # Fill in the missing team mates with a function that returns nothing
            while len(team1) != 5:
                tasks.append(self.do_nothing())

            for player in team2:
                tasks.append(self.get_global_kda(player))

            # Fill in the missing team mates with a function that returns nothing
            while len(team2) != 5:
                tasks.append(self.do_nothing())

            # Add in image creation task
            tasks.append(helper.create_match_image(team1_champs, team2_champs, team1_ranks, team2_ranks))

            # Run the tasks
            data = await asyncio.gather(*tasks)

            # Image
            buffer = data.pop()
            data1 = data[:5]
            data2 = data[5:]

            for pl, champ in zip(data1, team1_champs):
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

                # For teams total win rate and kda
                if pl[1] != "???" and float(pl[1]) > 50:
                    team1_overall[0] += 1               # num
                    team1_overall[1] += int(pl[1])      # level
                    team1_overall[2] += float(pl[2])    # win rate
                    team1_overall[3] += float(pl[3])    # kda

                # Add in champ stats
                if option == "-a" and can_use:
                    player_champ_data += await self.get_champ_stats_api(pl[0], champ, 1, lang=lang)

            match_data += "\n"
            player_champ_data += "\n"

            for pl, champ in zip(data2, team2_champs):
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

                # For teams total win rate and kda
                if pl[1] != "???" and float(pl[1]) > 50:
                    team2_overall[0] += 1  # num
                    team2_overall[1] += int(pl[1])    # level
                    team2_overall[2] += float(pl[2])  # win rate
                    team2_overall[3] += float(pl[3])  # kda

                # Add in champ stats
                if option == "-a" and can_use:
                    player_champ_data += await self.get_champ_stats_api(pl[0], champ, 1, lang=lang)

            # Adding team win rate's and kda's

            match_data += "\n\nAverage stats\n"
            ss1 = str('*{:18} Lv. {:3}  {:8}  {:6}\n')
            ss2 = str('*{:18} Lv. {:3}  {:8}  {:6}')
            team1_wr, team2_wr = 0, 0
            if team1_overall[0] != 0:
                team1_wr = round(team1_overall[2]/team1_overall[0], 2)
            if team2_overall[0] != 0:
                team2_wr = round(team2_overall[2]/team2_overall[0], 2)

            # no need to cal this is one team is 0
            if team1_wr != 0 and team2_wr != 0:
                if abs(team1_wr - team2_wr) >= 5.0:
                    if team1_wr > team2_wr:
                        ss1 = ss1.replace("*", "+")
                        ss2 = ss2.replace("*", "-")
                    else:
                        ss1 = ss1.replace("*", "-")
                        ss2 = ss2.replace("*", "+")

            if team1_overall[0] != 0:
                ss1 = ss1.format("Team1", str(int(team1_overall[1]/team1_overall[0])), str(team1_wr),
                                 str(round(team1_overall[3]/team1_overall[0], 2)))
                match_data += ss1
            if team2_overall[0] != 0:
                ss2 = ss2.format("Team2", str(int(team2_overall[1] / team2_overall[0])), str(team2_wr),
                                 str(round(team2_overall[3]/team2_overall[0], 2)))
                match_data += ss2
            file = discord.File(filename="Team.png", fp=buffer)
            await ctx.send("```diff\n" + match_data + "```", file=file)
            if "\n" in player_champ_data and value != -1:
                await ctx.send("```diff\n" + player_champ_data + "```")
            print(Fore.MAGENTA + f'{round(Process(getpid()).memory_info().rss/1024/1024, 2)} MB')

    # Returns simple stats based on the option they choose (champ_name, me, or elo)
    @commands.command(name='stats', aliases=['Statystyki'], pass_context=True, ignore_extra=False)
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def stats(self, ctx, player_name, option=None):
        lang = await helper.Lang.check_language(ctx=ctx)
        await helper.store_commands(ctx.author.id, "stats")

        # Maybe convert the player name
        if str(player_name) == "me":
            player_name = self.check_player_name(str(ctx.author.id))
        elif player_name[0] == "<" and player_name[1] == "@":  # 99% that someone has been mentioned
            player_name = player_name.replace("<", "").replace(">", "").replace("@", "").replace("!", "")
            if len(player_name) == 18:
                player_name = self.check_player_name(player_name)

        if player_name == "None":
            await ctx.send("You have not stored your IGN yet. To do so please use the store command like so: "
                           "`>>store Paladins_IGN`")
            return None

        if option is None:
            if not ctx.author.is_on_mobile():
                result = await self.get_player_stats_api(player_name, lang=lang)
                await ctx.send("```md\n" + result + "```")
            else:
                embeds = await self.get_player_stats_api_mobile(player_name, lang=lang)
                for embed in embeds:
                    await ctx.send(embed=embed)
        else:
            champ_name = await self.convert_champion_name(option)
            result = await self.get_champ_stats_api(player_name, champ_name, simple=0, lang=lang)
            try:
                await ctx.send(embed=result)
            except BaseException as e:
                await ctx.send(result)
                print("***Stupid error: " + str(e) + "result")

    # Stores Player's IGN for the bot to use
    @commands.command(name='store', pass_context=True, ignore_extra=False, aliases=["zapisz"])
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


# Add this class to the cog list
def setup(bot):
    bot.add_cog(PaladinsAPICog(bot))
