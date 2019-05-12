import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import requests
import my_utils as helper

from pyrez.api import PaladinsAPI
from pyrez.exceptions import PlayerNotFound
import json
import time

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

    DAMAGES = ["Cassie", "Kinessa", "Drogoz", "Bomb King", "Viktor", "Sha Lin", "Tyra", "Willo", "Lian", "Strix",
               "Vivian", "Dredge", "Imani"]
    FLANKS = ["Skye", "Buck", "Evie", "Androxus", "Maeve", "Lex", "Zhin", "Talus", "Moji", "Koga"]
    TANKS = ["Barik", "Fernando", "Ruckus", "Makoa", "Torvald", "Inara", "Ash", "Terminus", "Khan", "Atlas"]
    SUPPORTS = ["Grohk", "Grover", "Ying", "Mal Damba", "Seris", "Jenos", "Furia", "Pip"]

    dashes = "----------------------------------------"
    player_id_error = "Can't find the player: {} or their account is private. Please make sure the name is spelled " \
                      "correctly (Capitalization does not matter)."

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
    @classmethod
    def get_player_id(cls, player_name):
        player_name = player_name.lower()
        with open("player_ids") as json_f:
            player_ids = json.load(json_f)

        # This player is already in the dictionary and therefor we don't need to waste an api call to get the player id.
        if player_name in player_ids:
            return player_ids[player_name]
        else:
            try:
                player = paladinsAPI.getPlayer(player_name)
            except PlayerNotFound:
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
            return cls.player_id_error.format(player_name)
        info = paladinsAPI.getPlayer(player_id)

        # Overall Info
        ss = "Casual stats: \n{}\nName: {}\nAccount Level: {}\nWin Rate: {}% out of {} matches.\nTimes Deserted: {}\n\n"
        total = int(info.wins) + int(info.losses)
        wr = await cls.calc_win_rate(int(info.wins), total)
        ss = ss.format(cls.dashes, str(info.playerName), str(info.accountLevel), wr, str(total), str(info.leaves))

        # Ranked Info
        ss1 = "Ranked stats for Season {}:\n{}\nRank: {}\nTP: {} (position: {})\nWin Rate: {}% ({}-{})\n" \
              "Times Deserted: {}\n\n"
        ranked = info.rankedKeyboard
        win = int(ranked.wins)
        lose = int(ranked.losses)
        wr = await cls.calc_win_rate(win, win + lose)
        ss += ss1.format(str(ranked.currentSeason), cls.dashes, str(ranked.currentRank.getName()),
                         str(ranked.currentTrumpPoints), str(ranked.leaderboardIndex), wr, win, lose, str(ranked.leaves))

        # Extra info
        ss2 = "Extra details:\n{}\nAccount created on: {}\nLast login on: {}\nPlatform: {}\nMasteryLevel: {}\n" \
              "Steam Achievements completed: {}/58"
        ss += ss2.format(cls.dashes, str(info.createdDatetime).split()[0], str(info.lastLoginDatetime).split()[0],
                         str(info.platform), str(info.playedGods), str(info.totalAchievements))
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
            match_data = cls.player_id_error.format(player_name)
            embed = discord.Embed(
                description=match_data,
                colour=discord.colour.Color.dark_teal()
            )
            return embed
        stats = paladinsAPI.getChampionRanks(player_id)

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
    @commands.command(name='deck', pass_context=True)
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def deck(self, ctx, player_name, champ_name, deck_index=None):
        if str(player_name) == "me":
            player_name = self.check_player_name(str(ctx.author.id))
            if player_name == "None":
                await ctx.send("You have not stored your IGN yet. To do so please use the store command like so: "
                               "`>>store Paladins_IGN`")
                return None
        else:
            pass
        await helper.store_commands(ctx.author.id, "deck")
        async with ctx.channel.typing():
            player_id = self.get_player_id(player_name)

            if player_id == -1:
                match_data = self.player_id_error.format(player_name)
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

    @commands.command(name='history', pass_context=True)
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def history(self, ctx, player_name, amount=10, champ_name=None):
        if str(player_name) == "me":
            player_name = self.check_player_name(str(ctx.author.id))
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
                await ctx.send(self.player_id_error.format(player_name))
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
                    if count == 0:
                        return "Player does not have recent match data."
                    else:
                        break
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
    @commands.command(name='match')
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def match(self, ctx, player_name, match_id=-1):
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
            match_data = self.player_id_error.format(player_name)
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

            team1_data = []
            team2_data = []
            team1_champs = []
            team2_champs = []
            team1_parties = []
            team2_parties = []

            if match_id == -1 or match_id == match.matchId:
                match_data = paladinsAPI.getMatch(match.matchId)
                print(match.winStatus, match.matchMinutes, match.matchRegion,
                      str(match.mapName).replace("LIVE", ""))
                for pd in match_data:
                    # print(player_data)
                    if pd.taskForce == 1:
                        team1_data.append([pd.killsPlayer, pd.deaths, pd.assists, pd.damagePlayer, pd.damageTaken,
                                           pd.healing, pd.healingPlayerSelf, pd.objectiveAssists])
                        team1_champs.append(pd.referenceName)
                        team1_parties.append(pd.partyId)
                        # print("Team 1: " + str(pd.playerName) + str(pd.partyId))
                    else:
                        team2_data.append([pd.killsPlayer, pd.deaths, pd.assists, pd.damagePlayer, pd.damageTaken,
                                           pd.healing, pd.healingPlayerSelf, pd.objectiveAssists])
                        team2_champs.append(pd.referenceName)
                        team1_parties.append(pd.partyId)
                        # print("Team 2: " + str(pd.playerName) + str(pd.partyId))

                # Todo implement counting parties
                """
                party_id = 0
                party_status = []
                for player in team1_parties:
                    if team1_parties.count(player) > 2:

                    print(player)

                for player in team2_parties:
                    print(player)
                """

                buffer = await helper.create_history_image(team1_champs, team2_champs, team1_data, team2_data)
                file = discord.File(filename="Team.png", fp=buffer)
                await ctx.send("``` sup```", file=file)
                return None

                # ss = str('Champion: {}\nKDA: {} ({}-{}-{})\nDamage: {}\nDamage Taken: {}'
                #         '\nHealing: {} \nObjective Time: {}`\n')

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
            match_data = self.player_id_error.format(player_name)
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
                match_data = str('{}\'s {} match:\n\n').format(str(player_name), str(match.mapName).replace("LIVE", ""))
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
                await ctx.send(self.player_id_error.format(player_name))
                return None
            data = paladinsAPI.getPlayerStatus(player_id)

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

            # Data Format
            # {'Account_Level': 17, 'ChampionId': 2493, 'ChampionName': 'Koga', 'Mastery_Level': 10, 'Match': 795511902,
            # 'Queue': '424', 'SkinId': 0, 'Tier': 0, 'playerCreated': '11/10/2017 10:00:03 PM', 'playerId': '12368291',
            # 'playerName': 'NabbitOW', 'ret_msg': None, 'taskForce': 1, 'tierLosses': 0, 'tierWins': 0}
            try:
                players = paladinsAPI.getMatch(data.matchId, True)
            except BaseException as e:
                await ctx.send("An problem occurred. Please make sure you are not using this command on the event mode."
                               + str(e))
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
                name = str(player.playerName)  # Some names are not strings (example: symbols, etc.)
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

                # For teams total win rate and kda
                if pl[1] != "???" and float(pl[1]) > 50:
                    team1_overall[0] += 1               # num
                    team1_overall[1] += int(pl[1])       # level
                    team1_overall[2] += float(pl[2])    # win rate
                    team1_overall[3] += float(pl[3])    # kda

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

                # For teams total win rate and kda
                if pl[1] != "???" and float(pl[1]) > 50:
                    team2_overall[0] += 1  # num
                    team2_overall[1] += int(pl[1])    # level
                    team2_overall[2] += float(pl[2])  # win rate
                    team2_overall[3] += float(pl[3])  # kda

                # Add in champ stats
                if option == "-a" and can_use:
                    player_champ_data += await self.get_champ_stats_api(player, champ, 1)
                    # match_data += player_champ_data

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

            buffer = await helper.create_match_image(team1_champs, team2_champs, team1_ranks, team2_ranks)
            file = discord.File(filename="Team.png", fp=buffer)
            await ctx.send("```diff\n" + match_data + "```", file=file)
            if "\n" in player_champ_data and value != -1:
                await ctx.send("```diff\n" + player_champ_data + "```")

    # Returns simple stats based on the option they choose (champ_name, me, or elo)
    @commands.command(name='stats', aliases=['stat'])
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def stats(self, ctx, player_name, option=None):
        # Maybe convert the player name
        if str(player_name) == "me":
            player_name = self.check_player_name(str(ctx.author.id))
            if player_name == "None":
                await ctx.send("You have not stored your IGN yet. To do so please use the store command like so: "
                               "`>>store Paladins_IGN`")
                return None

        if option is None:
            result = await self.get_player_stats_api(player_name)
            await ctx.send("```md\n" + result + "```")
        elif option == "elo":
            await ctx.send("```Guru's site is currently under(as of 4/4/2019) development and until they finish "
                           "updating the site this bot can not get their elo data :(```")
            return None
            # result = await self.get_player_elo(player_name)
            # await ctx.send("```" + result + "```")
        else:
            champ_name = await self.convert_champion_name(option)
            result = await self.get_champ_stats_api(player_name, champ_name, simple=0)
            await ctx.send(embed=result)

    # Stores Player's IGN for the bot to use
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
