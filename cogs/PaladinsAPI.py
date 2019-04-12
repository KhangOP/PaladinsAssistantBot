import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import requests
import my_utils as helper

from pyrez.api import PaladinsAPI
import json

file_name = "token"
# Gets ID and KEY from a file
with open(file_name, 'r') as f:
    TOKEN = f.readline().strip()    # Does nothing
    PREFIX = f.readline()           # Does nothing
    ID = int(f.readline())
    KEY = f.readline()
f.close()

paladinsAPI = PaladinsAPI(devId=ID, authKey=KEY)


# All functions in this class use Pyrez wrapper to access Paladins API
class PaladinsAPICog(commands.Cog, name="Paladins API Commands"):
    """PaladinsAPICog"""

    def __init__(self, bot):
        self.bot = bot

    # Get the player id for a player based on their name. First it checks a dictionary and if they are not in there then
    # it does an API call to get the player's id. Then it writes that id to the dictionary. Helps save API calls.
    @classmethod
    def get_player_id(cls, player_name):
        player_name = player_name.lower()
        with open("player_ids") as json_f:
            player_ids = json.load(json_f)

        # This player is already in the dictionary and therefor we don't need to waste an api call to get the player id.
        if player_name in player_ids:
            return player_ids[player_name]
        else:
            player = paladinsAPI.getPlayer(player_name)
            if not player:  # invalid name
                return -1
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
        elif "End Times" in match_name:  # Event name
            return "End Times"
        elif "(Siege)" in match_name:  # Test Maps (WIP Thrones)
            return "Test Maps"
        else:
            return "Siege"

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
    async def get_global_kda(cls, player_name):
        url = "http://nonsocial.herokuapp.com/api/kda?player=" + player_name
        soup = BeautifulSoup(requests.get(url, headers={'Connection': 'close'}).text, 'html.parser')
        soup = str(soup.get_text())

        # Error checking to make sure that the player was found on the site
        if 'ERROR' in soup:
            error = [player_name, "???", "???", "???"]
            return error

        level = soup.split("(Level ")[1].split(")")[0]          # level
        kda = soup.split("- ")[1].split(" KDA")[0]              # KDA
        win_rate = soup.split("Win rate: ")[1].split("%")[0]    # Win rate

        stats = [player_name, level, win_rate, kda]

        return stats

    # Uses Paladins API to get overall stats for a player
    @classmethod
    async def get_player_stats_api(cls, player_name):
        # Player level, played hours, etc
        player_id = cls.get_player_id(player_name)
        if player_id == -1:
            return "Can't find the player: " + player_name + \
                   ". Please make sure the name is spelled correctly (Capitalization does not matter)."
        info = paladinsAPI.getPlayer(player_id)

        ss = ""

        # Basic Stats
        ss += "Casual stats: \n"
        ss += "Name: " + str(info.playerName) + "\n"
        ss += "Account Level: " + str(info.accountLevel) + "\n"
        total = int(info.wins) + int(info.losses)
        wr = await cls.calc_win_rate(int(info.wins), total)
        ss += "Win Rate: " + wr + "% out of " + str(total) + " matches.\n"
        ss += "Times Deserted: " + str(info.leaves) + "\n\n"

        # Ranked Info
        ranked = info.rankedKeyboard
        ss += "Ranked stats for Season " + str(ranked.currentSeason) + ":\n"
        # Rank (Masters, GM, Diamond, etc)
        ss += "Rank: " + str(ranked.currentRank) + "\nTP: " + str(ranked.currentTrumpPoints) + " Position: " + \
              str(ranked.leaderboardIndex) + "\n"

        win = int(ranked.wins)
        lose = int(ranked.losses)

        wr = await cls.calc_win_rate(win, win + lose)
        ss += "Win Rate: " + wr + "% (" + '{}-{}'.format(win, lose) + ")\n"
        ss += "Times Deserted: " + str(ranked.leaves) + "\n\n"

        # Extra info
        ss += "Extra details: \n"
        ss += "Account created on: " + str(info.createdDatetime).split()[0] + "\n"
        ss += "Last login on: " + str(info.lastLoginDatetime).split()[0] + "\n"
        ss += "Platform: " + str(info.platform) + "\n"
        data = info.json
        ss += "MasteryLevel: " + str(data["MasteryLevel"]) + "\n"
        ss += "Steam Achievements completed: " + str(info.totalAchievements) + "/58\n"

        return ss

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
    @classmethod
    async def get_champ_stats_api(cls, player_name, champ, simple):
        # Gets player id and error checks
        player_id = cls.get_player_id(player_name)
        if player_id == -1:
            if simple == 1:
                ss = str('*{:18} Lv. {:3}  {:7}   {:6}\n')
                ss = ss.format(champ, "???", "???", "???")
                return ss
            match_data = "Can't find the player: " + player_name + \
                         ". Please make sure the name is spelled correctly (Capitalization does not matter)."
            embed = discord.Embed(
                description=match_data,
                colour=discord.colour.Color.dark_teal()
            )
            return embed
        stats = paladinsAPI.getChampionRanks(player_id)

        if "Mal" in champ:
            champ = "Mal Damba"

        ss = ""
        t_wins = 0
        t_loses = 0
        t_kda = 0
        count = 0

        for stat in stats:
            count += 1
            wins = stat.wins
            losses = stat.losses
            kda = await cls.calc_kda(stat.kills, stat.deaths, stat.assists)
            # champ we want to get the stats on
            if stat.godName == champ:
                win_rate = await cls.calc_win_rate(wins, wins + losses)
                level = stat.godLevel

                last_played = str(stat.lastPlayed)
                if not last_played:  # Bought the champ but never played them
                    break

                ss = str('Champion: {} (Lv {})\nKDA: {} ({}-{}-{}) \nWin Rate: {}% ({}-{}) \nLast Played: {}')

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
                    elif (float(win_rate.replace(" %", ""))) < 50.00:
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
        win_rate = await cls.calc_win_rate(t_wins, t_wins + t_loses)
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

    '''Commands below ############################################################'''
    @commands.command(name='history', pass_context=True)
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def history(self, ctx, player_name, amount=10):
        if str(player_name) == "me":
            player_name = self.check_player_name(str(ctx.author.id))
            if player_name == "None":
                await ctx.send("You have not stored your IGN yet. To do so please use the store command like so: "
                               "`>>store Paladins_IGN`")
                return None
        else:
            pass
        await helper.store_commands(ctx.author.id, "history")
        async with ctx.channel.typing():
            if amount > 50 or amount <= 1:
                await ctx.send("Please enter an amount between 2-50")
                return None
            player_id = self.get_player_id(player_name)
            if player_id == -1:
                await ctx.send("Can't find the player: " + player_name +
                               ". Please make sure the name is spelled correctly (Capitalization does not matter).")
                return None
            paladins_data = paladinsAPI.getMatchHistory(player_id)
            # paladins_data = paladinsAPI.getMatchDetailsBatch(player_id) # Need to look into this
            count = 0
            match_data = ""
            match_data2 = ""
            for match in paladins_data:
                # Check to see if this player does have match history
                if match.playerName is None:
                    if count == 0:
                        return "Player does not have recent match data."
                    else:
                        break
                count += 1
                ss = str('+{:10}{:4}{:3}:00 {:9} {:9} {:5} ({}/{}/{})\n')
                kills = match.kills
                deaths = match.deaths
                assists = match.assists
                kda = await self.calc_kda(kills, deaths, assists)
                ss = ss.format(match.godName, match.winStatus, match.matchMinutes,
                               await self.convert_match_type(match.mapGame), match.matchId, kda, kills, deaths, assists)
                # Used for coloring
                if match.winStatus == "Loss":
                    ss = ss.replace("+", "-")

                if count > 30:
                    match_data2 += ss
                else:
                    match_data += ss
                if count == amount:
                    break

            title = str('{}\'s last {} matches:\n\n').format(str(player_name), count)
            title += str('{:11}{:4}  {:4} {:9} {:9} {:5} {}\n').format("Champion", "Win?", "Time", "Mode", "Match ID",
                                                                       "KDA",
                                                                       "Detailed")
            title += match_data
        await ctx.send("```diff\n" + title + "```")
        if amount > 30:
            await ctx.send("```diff\n" + match_data2 + "```")

    # Returns simple match history details
    @commands.command(name='last')
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def last(self, ctx, player_name, match_id=-1):
        if str(player_name) == "me":
            player_name = self.check_player_name(str(ctx.author.id))
            if player_name == "None":
                await ctx.send("You have not stored your IGN yet. To do so please use the store command like so: "
                               "`>>store Paladins_IGN`")
                return None
        else:
            pass
        await helper.store_commands(ctx.author.id, "last")
        player_id = self.get_player_id(player_name)

        if player_id == -1:
            match_data = "Can't find the player: " + player_name + \
                         ". Please make sure the name is spelled correctly (Capitalization does not matter)."
            embed = discord.Embed(
                description=match_data,
                colour=discord.colour.Color.dark_teal()
            )
            await ctx.send(embed=embed)
            return None

        paladins_data = paladinsAPI.getMatchHistory(player_id)
        for match in paladins_data:
            # Check to see if this player does have match history
            if match.playerName is None:
                break

            if match_id == -1 or match_id == match.matchId:
                match_data = str('{}\'s {} match:\n\n').format(str(player_name), str(match.mapGame).replace("LIVE", ""))
                ss = str('`Match Status: {} ({} mins)\nChampion: {}\nKDA: {} ({}-{}-{})\nDamage: {}\nDamage Taken: {}'
                         '\nHealing: {}\nSelf Healing: {}\nObjective Time: {}`\n')
                kills = match.kills
                deaths = match.deaths
                assists = match.assists
                kda = await self.calc_kda(kills, deaths, assists)
                match_data += ss.format(match.winStatus, match.matchMinutes, match.godName, kda, kills, deaths, assists,
                                        match.damage, match.damageTaken, match.healing, match.healingPlayerSelf,
                                        match.objectiveAssists)

                embed = discord.Embed(
                    description=match_data,
                    colour=discord.colour.Color.dark_teal()
                )

                embed.set_thumbnail(url=await helper.get_champ_image(match.godName))

                await ctx.send(embed=embed)
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

    # Gets details about a player in a current match using the Paladins API
    # Get stats for a player's current match.
    @commands.command(name='current', pass_context=True, aliases=["cur", 'c', "partida"])
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def current(self, ctx, player_name, option="-s"):
        # Maybe convert the player name
        if str(player_name) == "me":
            player_name = self.check_player_name(str(ctx.author.id))
            if player_name == "None":
                await ctx.send("You have not stored your IGN yet. To do so please use the store command like so: "
                               "`>>store Paladins_IGN`")
                return None
        else:
            pass
        value = -1
        if option == "-a":
            value = 1
        # can_use = await helper.store_commands(ctx.author.id, "current", value)
        can_use = True
        async with ctx.channel.typing():
            # Data Format
            # {'Match': 795950194, 'match_queue_id': 452, 'personal_status_message': 0, 'ret_msg': 0, 'status': 3,
            # 'status_string': 'In Game'}

            # Gets player id and error checks
            player_id = self.get_player_id(player_name)
            if player_id == -1:
                await ctx.send("Can't find the player: " + player_name +
                               ". Please make sure the name is spelled correctly (Capitalization does not matter).")
                return None
            data = paladinsAPI.getPlayerStatus(player_id)

            if data == 0:
                await ctx.send(str("Player " + player_name + " is not found."))
                return None
            if data.playerStatusId == 0:
                await ctx.send("Player is offline.")
                return None
            elif data.playerStatusId == 1:
                await ctx.send("Player is in lobby.")
                return None
            elif data.playerStatusId == 2:
                await ctx.send("Player in champion selection.")
                return None

            # match_queue_id = 424 = Siege
            # match_queue_id = 445 = Test Maps (NoneType) --> no json data
            # match_queue_id = 452 = Onslaught
            # match_queue_id = 469 = DTM
            # match_queue_id = 486 = Ranked (Invalid)

            current_match_queue_id = data.currentMatchQueueId

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

            # Data Format
            # {'Account_Level': 17, 'ChampionId': 2493, 'ChampionName': 'Koga', 'Mastery_Level': 10, 'Match': 795511902,
            # 'Queue': '424', 'SkinId': 0, 'Tier': 0, 'playerCreated': '11/10/2017 10:00:03 PM', 'playerId': '12368291',
            # 'playerName': 'NabbitOW', 'ret_msg': None, 'taskForce': 1, 'tierLosses': 0, 'tierWins': 0}
            try:
                players = paladinsAPI.getMatchPlayerDetails(data.currentMatchId)
            except BaseException as e:
                await ctx.send("An problem occurred. Please make sure you are not using this command on the event mode."
                               + str(e))
                return None
            # print(players)
            team1 = []
            team1_champs = []
            team2 = []
            team2_champs = []
            team1_ranks = []
            team2_ranks = []
            for player in players:
                # j = create_json(player)
                # name = (j["playerName"])
                name = str(player.playerName)  # Some names are not strings (example: symbols, etc.)

                # testing to see if character name is avaiable
                # print(player.playerName, player.godName) # Yes it is

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
            player_champ_data = ""
            match_data += player_name + " is in a " + match_string + " match."  # Match Type
            # print(match_data)
            match_data += str('\n\n{:18}  {:7}  {:8}  {:6}\n\n').format("Player name", "Level", "Win Rate", "KDA")
            player_champ_data = str('\n\n{:18}  {:7}  {:8}  {:6}\n\n').format("Champion name", "Level",
                                                                              "Win Rate", "KDA")

            for player, champ in zip(team1, team1_champs):
                pl = await self.get_global_kda(player)
                ss = str('*{:18} Lv. {:3}  {:8}  {:6}\n')
                ss = ss.format(pl[0], str(pl[1]), pl[2], pl[3])
                """This Block of code adds color based on Win Rate"""
                if "???" in pl[2]:
                    pass
                elif (float(pl[2].replace(" %", ""))) > 55.00:
                    ss = ss.replace("*", "+")
                elif (float(pl[2].replace(" %", ""))) < 50.00:
                    ss = ss.replace("*", "-")
                """^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"""
                match_data += ss

                # Add in champ stats
                if option == "-a" and can_use:
                    player_champ_data += await self.get_champ_stats_api(player, champ, 1)
                    # match_data += player_champ_data

            match_data += "\n"
            player_champ_data += "\n"

            for player, champ in zip(team2, team2_champs):
                # print(get_global_kda(player))
                pl = await self.get_global_kda(player)
                ss = str('*{:18} Lv. {:3}  {:8}  {:6}\n')
                ss = ss.format(pl[0], str(pl[1]), pl[2], pl[3])
                """This Block of code adds color based on Win Rate"""
                if "???" in pl[2]:
                    pass
                elif (float(pl[2].replace(" %", ""))) > 55.00:
                    ss = ss.replace("*", "+")
                elif (float(pl[2].replace(" %", ""))) < 50.00:
                    ss = ss.replace("*", "-")
                """^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"""
                match_data += ss

                # Add in champ stats
                if option == "-a" and can_use:
                    player_champ_data += await self.get_champ_stats_api(player, champ, 1)
                    # match_data += player_champ_data

            buffer = await helper.create_match_image(team1_champs, team2_champs, team1_ranks, team2_ranks)
            file = discord.File(filename="Team.png", fp=buffer)
            await ctx.send("```diff\n" + match_data + "```", file=file)
            if "\n" in player_champ_data and value != -1:
                await ctx.send("```diff\n" + player_champ_data + "```")

    # Returns simple stats based on the option they choose (champ_name, me, or elo)
    @commands.command(name='stats', aliases=['stat'])
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def stats(self, ctx, *args):
        await helper.store_commands(ctx.author.id, "stats")
        if len(args) > 3:
            await ctx.send("Too many arguments")

        # Maybe convert the player name
        if str(args[0]).lower() == "me":
            player_name = self.check_player_name(str(ctx.author.id))
            if player_name == "None":
                await ctx.send("You have not stored your IGN yet. To do so please use the store command like so: "
                               "`>>store Paladins_IGN`")
                return None
        else:
            player_name = args[0]

        # Just the name means they want base stats
        if len(args) == 1:
            result = await self.get_player_stats_api(player_name)
            await ctx.send("```" + result + "```")
        else:
            if str(args[1]).lower() == "elo":
                await ctx.send("```Guru's site is currently under(as of 4/4/2019) development and until they finish "
                               "updating the site this bot can not get their elo data :(```")
                return None
                # result = await self.get_player_elo(player_name)
                # await ctx.send("```" + result + "```")
            else:
                if len(args) == 2:
                    champ_name = str(args[1]).title()
                else:
                    champ_name = (str(args[1]) + " " + str(args[2])).title()
                result = await self.get_champ_stats_api(player_name, champ_name, simple=0)
                await ctx.send(embed=result)

    # Returns simple stats based on the option they choose (champ_name, me, or elo)
    @commands.command(name='store')
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
