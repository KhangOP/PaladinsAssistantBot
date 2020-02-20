from discord.ext import commands
from discord import Embed, colour, File

from PIL import Image, ImageFont, ImageDraw
from io import BytesIO

import my_utils as helper


# Hold commands that only the bot owner can use
class CurrentCog(commands.Cog, name="Current Command"):
    """Current Cog"""

    def __init__(self, bot):
        self.bot = bot

    # Gets details about a player in a current match using the Paladins API
    # Get stats for a player's current match.
    @commands.command(name='current', pass_context=True,
                      aliases=["Current", "partida", "Partida", "obecny", "Obecny"],
                      ignore_extra=False)
    @commands.cooldown(30, 30, commands.BucketType.user)
    async def current(self, ctx, player_name, option="-s"):
        lang = await self.bot.language.check_language(ctx=ctx)
        value = -1
        if option == "-a":
            value = 1
        can_use = await helper.store_commands(ctx.author.id, "current", value)

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

        async with ctx.channel.typing():
            # Data Format
            # {'Match': 795950194, 'match_queue_id': 452, 'personal_status_message': 0, 'ret_msg': 0, 'status': 3,
            # 'status_string': 'In Game'}

            # Gets player id and error checks
            player_id = self.get_player_id(player_name)
            if player_id == -1:
                await ctx.send(self.bot.cmd_lang_dict["general_error2"][lang].format(player_name))
                return None
            elif player_id == -2:
                await ctx.send("```Invalid platform name. Valid platform names are:\n1. Xbox\n2. PS4\n3. Switch```")
                return None
            elif player_id == -3:
                await ctx.send(
                    "Name overlap detected. Please look up your Paladins ID using the `>>console` command.")
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
            mobile_status = await self.bot.get_mobile_status(ctx=ctx)

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
            buffer = await self.create_match_image(team1_champs, team2_champs, team1_ranks, team2_ranks)

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

            file = File(filename="Team.png", fp=buffer)

            if not mobile_status:
                await ctx.send("```diff\n" + match_data + "```", file=file)
            else:  # Mobile version
                p1, p2 = team1_embed.pop()
                embed = Embed(
                    colour=colour.Color.blue(),
                    title=p1,
                    description=p2
                )
                for info in team1_embed:
                    embed.add_field(name=info[0], value=info[1], inline=False)

                p1, p2 = team2_embed.pop()
                embed2 = Embed(
                    colour=colour.Color.red(),
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
                        mobile_embed = Embed(
                            colour=colour.Color.blue(),
                            title="Team 1 Champion Stats:",
                            description="\u200b"
                        )
                        for info in mobile_data1:
                            mobile_embed.add_field(name=info[0], value=info[1], inline=False)
                        await ctx.send(embed=mobile_embed)

                    if mobile_data2:  # List contains data
                        mobile_embed2 = Embed(
                            colour=colour.Color.red(),
                            title="Team 2 Champion Stats:",
                            description="\u200b"
                        )
                        for info in mobile_data2:
                            mobile_embed2.add_field(name=info[0], value=info[1], inline=False)
                        await ctx.send(embed=mobile_embed2)

    # Todo needed by the current command as well
    async def get_champ_stats_api(self, player_name, champ, lang, mobile=False):
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
            embed = Embed(
                title=match_data,
                colour=colour.Color.dark_teal()
            )
            return embed
        elif player_id == -2:
            if simple == 1:
                if mobile:
                    return [champ, "???", "???", "???"]
                ss = str('*   {:15} Lv. {:3}  {:7}   {:6}\n')
                ss = ss.format(champ, "???", "???", "???")
                return ss
            embed = Embed(
                title="```Invalid platform name. Valid platform names are:\n1. Xbox\n2. PS4\n3. Switch```",
                colour=colour.Color.red()
            )
            return embed
        elif player_id == -3:
            if simple == 1:
                if mobile:
                    return [champ, "???", "???", "???"]
                ss = str('*   {:15} Lv. {:3}  {:7}   {:6}\n')
                ss = ss.format(champ, "???", "???", "???")
                return ss
            embed = Embed(
                title="Name overlap detected. Please look up your Paladins ID using the `>>console` command.",
                colour=colour.Color.red()
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
            embed = Embed(
                description=match_data,
                colour=colour.Color.dark_teal()
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
            embed = Embed(
                description=match_data,
                colour=colour.Color.dark_teal()
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
            embed = Embed(
                description=ss,
                colour=colour.Color.orange()
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
        embed = Embed(
            title=my_title,
            description=desc,
            colour=colour.Color.dark_teal()
        )
        embed.set_thumbnail(url=await helper.get_champ_image(champ))
        return embed

    # Creates a match image based on the two teams champions
    async def create_match_image(self, team1, team2, ranks1, ranks2):
        buffer1 = await self.create_team_image(team1, ranks1)
        buffer2 = await self.create_team_image(team2, ranks2)
        middle = await self.draw_match_vs()

        offset = 128

        image_size = 512
        match_image = Image.new('RGB', (image_size * len(team1), image_size * 2 + offset))

        # box – The crop rectangle, as a (left, upper, right, lower)- tuple.

        # Row 1
        match_image.paste(Image.open(buffer1), (0, 0, (image_size * len(team1)), image_size))

        # Middle row
        match_image.paste(Image.open(middle), (0, image_size, (image_size * len(team1)), image_size + offset))

        # Row 2
        match_image.paste(Image.open(buffer2),
                          (0, image_size + offset, (image_size * len(team1)), image_size * 2 + offset))

        #                                                                                   Base speed is 10 - seconds
        # match_image = match_image.resize((int(1280), int(576)), Image.ANTIALIAS)          # 5 seconds
        match_image = match_image.resize((1280, 576))  # 5 seconds (looks good)
        # match_image = match_image.resize((int(2560/3), int(1152/3)), Image.ANTIALIAS)     # 2-3 seconds
        # match_image = match_image.resize((int(2560 / 4), int(1152 / 4)), Image.ANTIALIAS) # 2-3 seconds
        # match_image.show()

        # Creates a buffer to store the image in
        final_buffer = BytesIO()

        # Store the pillow image we just created into the buffer with the PNG format
        match_image.save(final_buffer, "png")

        # seek back to the start of the buffer stream
        final_buffer.seek(0)

        return final_buffer

    # Creates an team image by using champion Icons
    @staticmethod
    async def create_team_image(champ_list, ranks):
        champion_images = []

        while len(champ_list) != 5:
            champ_list.append("?")

        for champ in champ_list:
            if champ != "?" and champ is not None:
                try:
                    champion_images.append(
                        Image.open("icons/champ_icons/{}.png".format(await helper.convert_champion_name_image(champ))))
                except FileNotFoundError:
                    image_size = 512
                    base = Image.new('RGB', (image_size, image_size), "black")
                    icon = Image.open("icons/unknown.png")
                    icon = icon.resize((512, 352), Image.ANTIALIAS)
                    base.paste(icon, (0, 80))
                    champion_images.append(base)
            else:
                image_size = 512
                base = Image.new('RGB', (image_size, image_size), "black")
                icon = Image.open("icons/unknown.png")
                icon = icon.resize((512, 352), Image.ANTIALIAS)
                base.paste(icon, (0, 160))

                # put text on image
                base_draw = ImageDraw.Draw(base)
                base_draw.text((140, 10), "Bot", font=ImageFont.truetype("arial", 140))
                champion_images.append(base)

        # Original Image size # print(width, height)
        image_size = 512
        scale = 1.5
        # champion_images.append(img.resize((image_size, image_size)))

        team_image = Image.new('RGB', (image_size * len(champion_images), image_size))
        for i, champ in enumerate(champion_images):
            team_image.paste(champ, (image_size * i, 0, image_size * (i + 1), image_size))

            # Only try to use ranked icons if its a ranked match
            if ranks:
                if i < len(ranks):  # make sure we don't go out of bounds
                    rank = Image.open("icons/ranks/" + ranks[i] + ".png")  # this works
                    width, height = rank.size
                    rank = rank.resize((int(width * scale), int(height * scale)))
                    team_image.paste(rank, (0 + (image_size * i), 0), rank)  # Upper Left

        # Testing
        # team_image.show()

        # Creates a buffer to store the image in
        final_buffer = BytesIO()

        # Store the pillow image we just created into the buffer with the PNG format
        team_image.save(final_buffer, "png")

        # seek back to the start of the buffer stream
        final_buffer.seek(0)

        return final_buffer

    # Draws a question in place of missing information for images
    @staticmethod
    async def draw_match_vs():
        base = Image.new('RGB', (2560, 128), "black")

        # put text on image
        base_draw = ImageDraw.Draw(base)
        base_draw.text((1248, 32), "VS", font=ImageFont.truetype("arial", 64))

        # Creates a buffer to store the image in
        final_buffer = BytesIO()

        # Store the pillow image we just created into the buffer with the PNG format
        base.save(final_buffer, "png")

        # seek back to the start of the buffer stream
        final_buffer.seek(0)

        return final_buffer


# Add this class to the cog list
def setup(bot):
    bot.add_cog(CurrentCog(bot))
