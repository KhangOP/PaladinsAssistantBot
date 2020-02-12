from PIL import Image, ImageFont, ImageDraw, ImageOps
import requests
from io import BytesIO
from datetime import datetime, timedelta
from pytz import timezone
import json
import time
import os
import math


"""
start = time.time()
"the code you want to placeholder stays here"
end = time.time()
print(end - start)
"""

'''This file servers to provide helper functions that our used in more than one other program.'''


class BotUtils:
    directory = 'user_info'
    usage = "usage"
    limits = "limits"
    current_uses_per_day = 4
    card_frames_dir = "icons/card_frames"

    command_list = ['last', 'stats', 'random', 'current', 'history', 'deck', 'match']
    command_limits = ['current']

    # Logs how many times someone uses a command
    # if used == -1 then don't worry about tracking limits
    async def store_commands(self, discord_id, command_name, used=-1):
        discord_id = str(discord_id)
        found = False
        for filename in os.listdir(self.directory):
            if filename == discord_id:
                found = True
                break
            else:
                continue

        # if we found the player in the player dir
        if found:
            with open(self.directory + "/" + discord_id) as json_f:
                user_info = json.load(json_f)
            try:
                user_info[self.usage][command_name] += 1
            except KeyError:  # Add keys that are missing
                user_info[self.usage][command_name] = 1

            if command_name == 'current' and used != -1:
                uses = user_info[self.limits]['current']
                # take away one use from the user
                if uses > 0:
                    user_info[self.limits]['current'] = (uses - used)
                else:
                    return False  # They can't use this command anymore today
            # Save changes to the file
            with open((self.directory + "/" + discord_id), 'w') as json_f:
                json.dump(user_info, json_f)

        # we did not find the user in the player dir so we need to make their file
        else:
            user_info = {self.usage: {}, self.limits: {}}

            # Set everything to zero since its a new user
            for command in self.command_list:
                if command == command_name:
                    user_info[self.usage][command] = 1
                else:
                    user_info[self.usage][command] = 0

            # Sets the limit of times a command can be used per day
            for command in self.command_limits:
                user_info[self.limits][command] = 4

            # Write data to file
            with open((self.directory + "/" + discord_id), 'w') as json_f:
                json.dump(user_info, json_f)

        return True

    # Gets ths command uses of a person based on their discord_id
    async def get_store_commands(self, discord_id):
        discord_id = str(discord_id)
        found = False
        for filename in os.listdir(self.directory):
            if filename == discord_id:
                found = True
                break
            else:
                continue

        # if we found the player in the player dir
        if found:
            with open(self.directory + "/" + discord_id) as personal_json:
                user_info = json.load(personal_json)
                return user_info[self.usage]
        # we did not find the user in the player dir so we need to make fun of them
        else:
            return "Lol, you trying to call this command without ever using the bot."

    # Est Time zone for logging function calls
    @classmethod
    async def get_est_time(cls):
        # using just timezone 'EST' does not include daylight savings
        return datetime.now(timezone('US/Eastern')).strftime("%H:%M:%S %m/%d/%Y")

    # Resets command uses back to 4
    async def reset_command_uses(self):
        for filename in os.listdir(self.directory):
            with open(self.directory + "/" + filename) as json_f:
                user_info = json.load(json_f)
                user_info[self.limits]['current'] = 4  # Reset
            # Save changes to the file
            with open((self.directory + "/" + filename), 'w') as json_d:
                json.dump(user_info, json_d)
        print("Finished resetting command uses.")

    # Gets minutes left in the hour
    @classmethod
    async def get_second_until_hour(cls):
        minutes_left_in_hour = 60 - datetime.now().minute   # Get minutes left until the next hour
        minutes_left_in_hour = minutes_left_in_hour - 5     # (5 minutes before the hour)
        if minutes_left_in_hour < 0:
            return 0
        return minutes_left_in_hour

    # This function will get the number of second until 6est. when I want to reset data
    @classmethod
    async def get_seconds_until_reset(cls):
        """Get the number of seconds until 6am est."""
        # code from----> http://jacobbridges.github.io/post/how-many-seconds-until-midnight/
        tomorrow = datetime.now() + timedelta(1)
        midnight = datetime(year=tomorrow.year, month=tomorrow.month,
                            day=tomorrow.day, hour=6, minute=0, second=0)
        hours = str(int((midnight - datetime.now()).seconds / (60 * 60)))
        print("Time until reset: {} hours.".format(hours))
        return (midnight - datetime.now()).seconds

    # Converts champion names so they can be used to fetch champion images in a url
    @classmethod
    async def convert_champion_name(cls, champ_name, special=False):
        champ_name = champ_name.lower()
        # These are the special cases that need to be checked
        if "bomb" in champ_name:
            return "bomb-king"
        if "mal" in champ_name:
            if special:
                return "mal'damba"
            else:
                return "maldamba"
        if "sha" in champ_name:
            return "sha-lin"
        # else return the name passed in since its already correct
        return champ_name

    # Gets a url to the image of champion's name passed in
    async def get_champ_image(self, champ_name):
        champ_name = await self.convert_champion_name(champ_name)
        url = "https://raw.githubusercontent.com/EthanHicks1/PaladinsAssistantBot/master/icons/champ_icons/{}.png"\
            .format(champ_name)
        return url


# Todo split ------------------ above is utils class >< below is image cogs

# Creates an team image by using champion Icons
async def create_team_image(champ_list, ranks):
    champion_images = []

    while len(champ_list) != 5:
        champ_list.append("?")

    for champ in champ_list:
        if champ != "?" and champ is not None:
            try:
                champion_images.append(Image.open("icons/champ_icons/{}.png".format(await convert_champion_name(champ))))
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
        team_image.paste(champ, (image_size*i, 0, image_size*(i+1), image_size))

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


# Creates a match image based on the two teams champions
async def create_match_image(team1, team2, ranks1, ranks2):
    buffer1 = await create_team_image(team1, ranks1)
    buffer2 = await create_team_image(team2, ranks2)
    middle = await draw_match_vs()

    offset = 128

    image_size = 512
    match_image = Image.new('RGB', (image_size * len(team1), image_size*2 + offset))

    # box – The crop rectangle, as a (left, upper, right, lower)- tuple.

    # Row 1
    match_image.paste(Image.open(buffer1), (0, 0, (image_size*len(team1)), image_size))

    # Middle row
    match_image.paste(Image.open(middle), (0, image_size, (image_size * len(team1)), image_size+offset))

    # Row 2
    match_image.paste(Image.open(buffer2), (0, image_size + offset, (image_size*len(team1)), image_size*2 + offset))

    #                                                                                       Base speed is 10 - seconds
    # match_image = match_image.resize((int(1280), int(576)), Image.ANTIALIAS)              # 5 seconds
    match_image = match_image.resize((1280, 576))                                           # 5 seconds (looks good)
    # match_image = match_image.resize((int(2560/3), int(1152/3)), Image.ANTIALIAS)         # 2-3 seconds
    # match_image = match_image.resize((int(2560 / 4), int(1152 / 4)), Image.ANTIALIAS)     # 2-3 seconds
    # match_image.show()

    # Creates a buffer to store the image in
    final_buffer = BytesIO()

    # Store the pillow image we just created into the buffer with the PNG format
    match_image.save(final_buffer, "png")

    # seek back to the start of the buffer stream
    final_buffer.seek(0)

    return final_buffer


# Draws a question in place of missing information for images
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


# Creates a match image based on the two teams champions
async def create_history_image(team1, team2, t1_data, t2_data, p1, p2, match_data, colored):
    shrink = 140
    image_size_y = 512 - shrink*2
    image_size_x = 512
    offset = 5
    history_image = Image.new('RGB', (image_size_x*9, image_size_y*12 + 264))

    # Adds the top key panel
    key = await create_player_key_image(image_size_x, image_size_y, colored)
    history_image.paste(key, (0, 0))

    # Creates middle panel
    mid_panel = await create_middle_info_panel(match_data)
    history_image.paste(mid_panel, (0, 1392-40))

    # Adding in player data
    for i, (champ, champ2) in enumerate(zip(team1, team2)):
        try:
            champ_image = Image.open("icons/champ_icons/{}.png".format(await convert_champion_name(champ)))
        except FileNotFoundError:
            champ_image = Image.open("icons/temp_card_art.png")
        border = (0, shrink, 0, shrink)  # left, up, right, bottom
        champ_image = ImageOps.crop(champ_image, border)
        # history_image.paste(champ_image, (0, image_size*i, image_size, image_size*(i+1)))
        player_panel = await create_player_stats_image(champ_image, t1_data[i], i, p1, colored)
        history_image.paste(player_panel, (0, (image_size_y+10)*i+132))

        # Second team
        try:
            champ_image = Image.open("icons/champ_icons/{}.png".format(await convert_champion_name(champ2)))
        except FileNotFoundError:
            champ_image = Image.open("icons/temp_card_art.png")
        border = (0, shrink, 0, shrink)  # left, up, right, bottom
        champ_image = ImageOps.crop(champ_image, border)

        player_panel = await create_player_stats_image(champ_image, t2_data[i], i+offset-1, p2, colored)
        history_image.paste(player_panel, (0, image_size_y * (i+offset) + 704))

    # Base speed is 10 - seconds
    history_image = history_image.resize((4608//2, 3048//2), Image.ANTIALIAS)           # 5 seconds
    # history_image = history_image.resize((4608 // 4, 3048 // 4), Image.ANTIALIAS)     # 2.5 secs but bad looking

    # Creates a buffer to store the image in
    final_buffer = BytesIO()

    # Store the pillow image we just created into the buffer with the PNG format
    history_image.save(final_buffer, "png")

    # seek back to the start of the buffer stream
    final_buffer.seek(0)

    return final_buffer


async def create_middle_info_panel(md):  # update this section
    middle_panel = Image.new('RGB', (512*9, 512), color=(217, 247, 247))

    # Adding in map to image
    map_name = map_file_name = (md[3].strip().replace("Ranked ", "").replace(" (TDM)", "").replace(" (Onslaught)", "")
                                .replace(" (Siege)", "")).replace("Practice ", "")
    if "WIP" in map_name:
        map_file_name = "test_maps"
        map_name = map_name.replace("WIP ", "")

    # Needed to catch weird-unknown map modes
    try:
        match_map = Image.open("icons/maps/{}.png".format(map_file_name.lower().replace(" ", "_").replace("'", "")))
    except FileNotFoundError:
        match_map = Image.open("icons/maps/test_maps.png")

    match_map = match_map.resize((512*2, 512), Image.ANTIALIAS)
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

    center = (512/2 - 130/2)
    center2 = (512/2 - 80/2)
    # VS
    draw_panel.text((512 * 5-150, center), "VS", font=ImageFont.truetype("arialbd", 130), fill=(0, 0, 0))

    # Team 2
    draw_panel.text((512 * 4 + rs, 372), "Team 2 Score: ", font=ImageFont.truetype("arial", 100), fill=(0, 0, 0))
    draw_panel.text((512 * 4 + rs * 8, 372), str(md[5]), font=ImageFont.truetype("arialbd", 100), fill=(0, 0, 0))

    #  add in banned champs if it's a ranked match
    if md[6] is not None:
        # Ranked bans
        draw_panel.text((512 * 5 + rs * 8, center2), "Bans:", font=ImageFont.truetype("arialbd", 80), fill=(0, 0, 0))

        # Team 1 Bans
        try:
            champ_image = Image.open("icons/champ_icons/{}.png".format(await convert_champion_name(str(md[6]))))
            champ_image = champ_image.resize((200, 200))
            middle_panel.paste(champ_image, (512 * 7 + rs, ds))
        except FileNotFoundError:
            pass

        try:
            champ_image = Image.open("icons/champ_icons/{}.png".format(await convert_champion_name(str(md[7]))))
            champ_image = champ_image.resize((200, 200))
            middle_panel.paste(champ_image, (512 * 7 + rs + 240, ds))
        except FileNotFoundError:
            pass

        # Team 2 Bans
        try:
            champ_image = Image.open("icons/champ_icons/{}.png".format(await convert_champion_name(str(md[8]))))
            champ_image = champ_image.resize((200, 200))
            middle_panel.paste(champ_image, (512 * 7 + rs, ds+232))
        except FileNotFoundError:
            pass

        try:
            champ_image = Image.open("icons/champ_icons/{}.png".format(await convert_champion_name(str(md[9]))))
            champ_image = champ_image.resize((200, 200))
            middle_panel.paste(champ_image, (512 * 7 + rs + 240, ds+232))
        except FileNotFoundError:
            pass

    return middle_panel


async def create_player_stats_image(champ_icon, champ_stats, index, party, color=False):
    shrink = 140
    offset = 10
    image_size_y = 512 - shrink * 2
    img_x = 512
    middle = image_size_y/2 - 50
    im_color = (175, 238, 238, 0) if index % 2 == 0 else (196, 242, 242, 0)
    # color = (175, 238, 238)   # light blue
    # color = (196, 242, 242)     # lighter blue
    champ_stats_image = Image.new('RGBA', (img_x*9, image_size_y+offset*2), color=im_color)

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
    base_draw.text((img_x + 20, middle-40), str(champ_stats[0]), font=ImageFont.truetype("arialbd", 80), fill=(0, 0, 0))
    base_draw.text((img_x + 20, middle+60), str(champ_stats[1]), font=ImageFont.truetype("arial", 80), fill=(0, 0, 0))

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


# Creates the text at the top of the image
async def create_player_key_image(x, y, color=False):
    key = Image.new('RGB', (x * 9, y-100), color=(112, 225, 225))
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
