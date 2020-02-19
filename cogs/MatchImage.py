from discord.ext import commands
from discord import Embed, colour, File

from pyrez.exceptions import NotFound, MatchException

from PIL import Image, ImageFont, ImageDraw, ImageOps
from io import BytesIO

import my_utils as helper


class MatchCog(commands.Cog, name="Match Command"):
    """Match Cog"""
    def __init__(self, bot):
        self.bot = bot

    # Returns an image of a match with player details
    @commands.command(name='match', pass_context=True, ignore_extra=False, aliases=["Match", "mecz", "Mecz"])
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def match(self, ctx, player_name, match_id=None, colored="-b"):
        lang = await self.bot.language.check_language(ctx=ctx)
        await helper.store_commands(ctx.author.id, "match")

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

        player_id = self.get_player_id(player_name)

        if player_id == -1:
            match_data = self.bot.cmd_lang_dict["general_error2"][lang].format(player_name)
            embed = Embed(
                title=match_data,
                colour=colour.Color.dark_teal()
            )
            await ctx.send(embed=embed)
            return None
        elif player_id == -2:
            embed = Embed(
                title="```Invalid platform name. Valid platform names are:\n1. Xbox\n2. PS4\n3. Switch```",
                colour=colour.Color.red()
            )
            await ctx.send(embed=embed)
            return None
        elif player_id == -3:
            embed = Embed(
                title="Name overlap detected. Please look up your Paladins ID using the `>>console` command.",
                colour=colour.Color.red()
            )
            await ctx.send(embed=embed)
            return None

        async with ctx.channel.typing():
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

                    buffer = await self.create_history_image(team1_champs, team2_champs, team1_data, team2_data,
                                                             team1_parties, team2_parties, (match_info + temp), color)

                    file = File(filename="TeamMatch.png", fp=buffer)

                    await ctx.send("```You are an amazing person!```", file=file)
                    return None

            # If the match id could not be found
            embed = Embed(
                description="Could not find a match with the match id: " + str(match_id),
                colour=colour.Color.dark_teal()
            )

            # If player has not played recently
            if match_id == -1:
                embed.description = "Player does not have recent match data."

            await ctx.send(embed=embed)

    # Creates a match image based on the two teams champions
    async def create_history_image(self, team1, team2, t1_data, t2_data, p1, p2, match_data, colored):
        shrink = 140
        image_size_y = 512 - shrink * 2
        image_size_x = 512
        offset = 5
        history_image = Image.new('RGB', (image_size_x * 9, image_size_y * 12 + 264))

        # Adds the top key panel
        key = await self.create_player_key_image(image_size_x, image_size_y, colored)
        history_image.paste(key, (0, 0))

        # Creates middle panel
        mid_panel = await self.create_middle_info_panel(match_data)
        history_image.paste(mid_panel, (0, 1392 - 40))

        # Adding in player data
        for i, (champ, champ2) in enumerate(zip(team1, team2)):
            try:
                champ_image = Image.open("icons/champ_icons/{}.png".format(
                    await helper.convert_champion_name_image(champ)))
            except FileNotFoundError:
                champ_image = Image.open("icons/temp_card_art.png")
            border = (0, shrink, 0, shrink)  # left, up, right, bottom
            champ_image = ImageOps.crop(champ_image, border)
            # history_image.paste(champ_image, (0, image_size*i, image_size, image_size*(i+1)))
            player_panel = await self.create_player_stats_image(champ_image, t1_data[i], i, p1, colored)
            history_image.paste(player_panel, (0, (image_size_y + 10) * i + 132))

            # Second team
            try:
                champ_image = Image.open("icons/champ_icons/{}.png".format(
                    await helper.convert_champion_name_image(champ2)))
            except FileNotFoundError:
                champ_image = Image.open("icons/temp_card_art.png")
            border = (0, shrink, 0, shrink)  # left, up, right, bottom
            champ_image = ImageOps.crop(champ_image, border)

            player_panel = await self.create_player_stats_image(champ_image, t2_data[i], i + offset - 1, p2, colored)
            history_image.paste(player_panel, (0, image_size_y * (i + offset) + 704))

        # Base speed is 10 - seconds
        history_image = history_image.resize((4608 // 2, 3048 // 2), Image.ANTIALIAS)  # 5 seconds
        # history_image = history_image.resize((4608 // 4, 3048 // 4), Image.ANTIALIAS)     # 2.5 secs but bad looking

        # Creates a buffer to store the image in
        final_buffer = BytesIO()

        # Store the pillow image we just created into the buffer with the PNG format
        history_image.save(final_buffer, "png")

        # seek back to the start of the buffer stream
        final_buffer.seek(0)

        return final_buffer

    # Creates the text at the top of the image
    @staticmethod
    async def create_player_key_image(x, y, color=False):
        key = Image.new('RGB', (x * 9, y - 100), color=(112, 225, 225))
        base_draw = ImageDraw.Draw(key)
        # ss = "Player Credits K/D/A  Damage  Taken  Objective Time  Shielding  Healing"
        base_draw.text((20, 0), "Champion", font=ImageFont.truetype("arial", 80), fill=(0, 0, 0))
        base_draw.text((x + 20, 0), "Player", font=ImageFont.truetype("arial", 80), fill=(0, 0, 0))

        # Parties
        fill = (128, 0, 128) if color else (0, 0, 0)
        base_draw.text((x + 750, 0), "P", font=ImageFont.truetype("arial", 100), fill=fill)

        # Credits/Gold earned
        fill = (218, 165, 32) if color else (0, 0, 0)
        base_draw.text((x + 900, 0), "Credits", font=ImageFont.truetype("arial", 80), fill=fill)

        # KDA
        fill = (101, 33, 67) if color else (0, 0, 0)
        base_draw.text((x + 1300, 0), "K/D/A", font=ImageFont.truetype("arial", 80), fill=fill)

        # Damage done
        fill = (255, 0, 0) if color else (0, 0, 0)
        base_draw.text((x + 1830, 0), "Damage", font=ImageFont.truetype("arial", 80), fill=fill)

        # Damage taken
        fill = (220, 20, 60) if color else (0, 0, 0)
        base_draw.text((x + 2350, 0), "Taken", font=ImageFont.truetype("arial", 80), fill=fill)

        # Objective time
        fill = (159, 105, 52) if color else (0, 0, 0)
        base_draw.text((x + 2800, 0), "Objective", font=ImageFont.truetype("arial", 60), fill=fill)
        base_draw.text((x + 2850, 60), "Time", font=ImageFont.truetype("arial", 60), fill=fill)

        # Shielding
        fill = (0, 51, 102) if color else (0, 0, 0)
        base_draw.text((x + 3150, 0), "Shielding", font=ImageFont.truetype("arial", 80), fill=fill)

        # Healing
        fill = (0, 128, 0) if color else (0, 0, 0)
        base_draw.text((x + 3600, 0), "Healing", font=ImageFont.truetype("arial", 80), fill=fill)

        return key

    @staticmethod
    async def create_middle_info_panel(md):
        middle_panel = Image.new('RGB', (512 * 9, 512), color=(217, 247, 247))

        # Adding in map to image
        map_name = map_file_name = (
            md[3].strip().replace("Ranked ", "").replace(" (TDM)", "").replace(" (Onslaught)", "")
            .replace(" (Siege)", "")).replace("Practice ", "")
        if "WIP" in map_name:
            map_file_name = "test_maps"
            map_name = map_name.replace("WIP ", "")

        # Needed to catch weird-unknown map modes
        try:
            match_map = Image.open("icons/maps/{}.png".format(map_file_name.lower().replace(" ", "_").replace("'", "")))
        except FileNotFoundError:
            match_map = Image.open("icons/maps/test_maps.png")

        match_map = match_map.resize((512 * 2, 512), Image.ANTIALIAS)
        middle_panel.paste(match_map, (0, 0))

        # Preparing the panel to draw on
        draw_panel = ImageDraw.Draw(middle_panel)

        # Add in match information
        ds = 50  # Down Shift
        rs = 20  # Right Shift
        draw_panel.text((512 * 2 + rs, 0 + ds), str(md[0]), font=ImageFont.truetype("arial", 100), fill=(0, 0, 0))
        draw_panel.text((512 * 2 + rs, 100 + ds), (str(md[1]) + " minutes"), font=ImageFont.truetype("arial", 100),
                        fill=(0, 0, 0))
        draw_panel.text((512 * 2 + rs, 200 + ds), str(md[2]), font=ImageFont.truetype("arial", 100), fill=(0, 0, 0))
        draw_panel.text((512 * 2 + rs, 300 + ds), str(map_name), font=ImageFont.truetype("arial", 100), fill=(0, 0, 0))

        # Right shift
        rs = 100
        # Team 1
        draw_panel.text((512 * 4 + rs, ds), "Team 1 Score: ", font=ImageFont.truetype("arial", 100), fill=(0, 0, 0))
        draw_panel.text((512 * 4 + rs * 8, ds), str(md[4]), font=ImageFont.truetype("arialbd", 100), fill=(0, 0, 0))

        center = (512 / 2 - 130 / 2)
        center2 = (512 / 2 - 80 / 2)
        # VS
        draw_panel.text((512 * 5 - 150, center), "VS", font=ImageFont.truetype("arialbd", 130), fill=(0, 0, 0))

        # Team 2
        draw_panel.text((512 * 4 + rs, 372), "Team 2 Score: ", font=ImageFont.truetype("arial", 100), fill=(0, 0, 0))
        draw_panel.text((512 * 4 + rs * 8, 372), str(md[5]), font=ImageFont.truetype("arialbd", 100), fill=(0, 0, 0))

        #  add in banned champs if it's a ranked match
        if md[6] is not None:
            # Ranked bans
            draw_panel.text((512 * 5 + rs * 8, center2), "Bans:", font=ImageFont.truetype("arialbd", 80),
                            fill=(0, 0, 0))

            # Team 1 Bans
            try:
                champ_image = Image.open("icons/champ_icons/{}.png".format(
                    await helper.convert_champion_name_image(str(md[6]))))
                champ_image = champ_image.resize((200, 200))
                middle_panel.paste(champ_image, (512 * 7 + rs, ds))
            except FileNotFoundError:
                pass

            try:
                champ_image = Image.open("icons/champ_icons/{}.png".format(
                    await helper.convert_champion_name_image(str(md[7]))))
                champ_image = champ_image.resize((200, 200))
                middle_panel.paste(champ_image, (512 * 7 + rs + 240, ds))
            except FileNotFoundError:
                pass

            # Team 2 Bans
            try:
                champ_image = Image.open("icons/champ_icons/{}.png".format(
                    await helper.convert_champion_name_image(str(md[8]))))
                champ_image = champ_image.resize((200, 200))
                middle_panel.paste(champ_image, (512 * 7 + rs, ds + 232))
            except FileNotFoundError:
                pass

            try:
                champ_image = Image.open("icons/champ_icons/{}.png".format(
                    await helper.convert_champion_name_image(str(md[9]))))
                champ_image = champ_image.resize((200, 200))
                middle_panel.paste(champ_image, (512 * 7 + rs + 240, ds + 232))
            except FileNotFoundError:
                pass

        return middle_panel

    @staticmethod
    async def create_player_stats_image(champ_icon, champ_stats, index, party, color=False):
        shrink = 140
        offset = 10
        image_size_y = 512 - shrink * 2
        img_x = 512
        middle = image_size_y / 2 - 50
        im_color = (175, 238, 238, 0) if index % 2 == 0 else (196, 242, 242, 0)
        # color = (175, 238, 238)   # light blue
        # color = (196, 242, 242)     # lighter blue
        champ_stats_image = Image.new('RGBA', (img_x * 9, image_size_y + offset * 2), color=im_color)

        champ_stats_image.paste(champ_icon, (offset, offset))

        platform = champ_stats[10]
        if platform == "XboxLive":
            platform_logo = Image.open("icons/xbox_logo.png").resize((100, 100), Image.ANTIALIAS)
            platform_logo = platform_logo.convert("RGBA")
            champ_stats_image.paste(platform_logo, (img_x + 175, int(middle) + 60), platform_logo)
        elif platform == "Nintendo Switch":
            platform_logo = Image.open("icons/switch_logo.png")
            width, height = platform_logo.size
            scale = .15
            platform_logo = platform_logo.resize((int(width * scale), int(height * scale)), Image.ANTIALIAS)
            platform_logo = platform_logo.convert("RGBA")
            champ_stats_image.paste(platform_logo, (img_x + 135, int(middle) + 45), platform_logo)
        elif platform == "PSN":
            platform_logo = Image.open("icons/ps4_logo.png").resize((100, 100), Image.ANTIALIAS)
            platform_logo = platform_logo.convert("RGBA")
            champ_stats_image.paste(platform_logo, (img_x + 175, int(middle) + 60), platform_logo)
        # For future if I want to add a PC icon
        # else:
        #    print("PC")

        # if platform_logo:
        #    platform_logo = platform_logo.convert("RGBA")
        #    champ_stats_image.paste(platform_logo, (img_x + 175, int(middle)+60), platform_logo)
        #    # champ_stats_image.show()

        base_draw = ImageDraw.Draw(champ_stats_image)

        # Private account or unknown
        if str(champ_stats[0]) == "":
            champ_stats[0] = "*****"

        # Player name and champion name
        base_draw.text((img_x + 20, middle - 40), str(champ_stats[0]), font=ImageFont.truetype("arialbd", 80),
                       fill=(0, 0, 0))
        base_draw.text((img_x + 20, middle + 60), str(champ_stats[1]), font=ImageFont.truetype("arial", 80),
                       fill=(0, 0, 0))

        # Parties
        fill = (128, 0, 128) if color else (0, 0, 0)
        base_draw.text((img_x + 750, middle), party[champ_stats[9]], font=ImageFont.truetype("arial", 100), fill=fill)

        # Credits/Gold earned
        fill = (218, 165, 32) if color else (0, 0, 0)
        base_draw.text((img_x + 900, middle), str(champ_stats[2]), font=ImageFont.truetype("arial", 100), fill=fill)

        # KDA
        fill = (101, 33, 67) if color else (0, 0, 0)
        base_draw.text((img_x + 1300, middle), str(champ_stats[3]), font=ImageFont.truetype("arial", 100), fill=fill)

        # Damage done
        fill = (255, 0, 0) if color else (0, 0, 0)
        base_draw.text((img_x + 1830, middle), str(champ_stats[4]), font=ImageFont.truetype("arial", 100), fill=fill)

        # Damage taken
        fill = (220, 20, 60) if color else (0, 0, 0)
        base_draw.text((img_x + 2350, middle), str(champ_stats[5]), font=ImageFont.truetype("arial", 100), fill=fill)

        # Objective time
        fill = (159, 105, 52) if color else (0, 0, 0)
        base_draw.text((img_x + 2850, middle), str(champ_stats[6]), font=ImageFont.truetype("arial", 100), fill=fill)

        # Shielding
        fill = (0, 51, 102) if color else (0, 0, 0)
        base_draw.text((img_x + 3150, middle), str(champ_stats[7]), font=ImageFont.truetype("arial", 100), fill=fill)

        # Healing
        fill = (0, 128, 0) if color else (0, 0, 0)
        base_draw.text((img_x + 3600, middle), str(champ_stats[8]), font=ImageFont.truetype("arial", 100), fill=fill)

        return champ_stats_image


# Add this class to the cog list
def setup(bot):
    bot.add_cog(MatchCog(bot))
