from PIL import Image, ImageFont, ImageDraw
import requests
from io import BytesIO
from datetime import datetime, timedelta
from pytz import timezone
import json
import os

'''This file servers to provide helper functions that our used in more than one other program.'''


directory = 'user_info'
usage = "usage"
limits = "limits"
current_uses_per_day = 4

command_list = ['last', 'stats', 'random', 'current', 'history']
command_limits = ['current']


# Logs how many times someone uses a command
async def store_commands(discord_id, command_name, used=-1):  # if used == -1 then don't worry about tracking limits
    discord_id = str(discord_id)
    found = False
    for filename in os.listdir(directory):
        if filename == discord_id:
            found = True
            break
        else:
            continue

    # if we found the player in the player dir
    if found:
        with open(directory + "/" + discord_id) as json_f:
            user_info = json.load(json_f)

        user_info[usage][command_name] += 1

        if command_name == 'current' and used != -1:
            uses = user_info[limits]['current']
            # take away one use from the user
            if uses > 0:
                user_info[limits]['current'] = (uses - used)
            else:
                return False  # They can't use this command anymore today
        # Save changes to the file
        with open((directory + "/" + discord_id), 'w') as json_f:
            json.dump(user_info, json_f)

    # we did not find the user in the player dir so we need to make their file
    else:
        user_info = {usage: {}, limits: {}}

        # Set everything to zero since its a new user
        for command in command_list:
            if command == command_name:
                user_info[usage][command] = 1
            else:
                user_info[usage][command] = 0

        # Sets the limit of times a command can be used per day
        for command in command_limits:
            user_info[limits][command] = 4

        # Write data to file
        with open((directory + "/" + discord_id), 'w') as json_f:
            json.dump(user_info, json_f)

    return True


# Est Time zone for logging function calls
async def get_est_time():
    # using just timezone 'EST' does not include daylight savings
    return datetime.now(timezone('US/Eastern')).strftime("%H:%M:%S %m/%d/%Y")


# Resets command uses back to 4
async def reset_command_uses():
    for filename in os.listdir(directory):
        with open(directory + "/" + filename) as json_f:
            user_info = json.load(json_f)
            user_info[limits]['current'] = 4  # Reset
        # Save changes to the file
        with open((directory + "/" + filename), 'w') as json_d:
            json.dump(user_info, json_d)
    print("Finished resetting command uses.")


# This function will get the number of second until 6est. when I want to reset data
async def get_seconds_until_reset():
    """Get the number of seconds until 6am est."""
    # code from----> http://jacobbridges.github.io/post/how-many-seconds-until-midnight/
    tomorrow = datetime.now() + timedelta(1)
    midnight = datetime(year=tomorrow.year, month=tomorrow.month,
                        day=tomorrow.day, hour=6, minute=0, second=0)
    hours = str(int((midnight - datetime.now()).seconds / (60 * 60)))
    print("Time until reset: {} hours.".format(hours))
    return (midnight - datetime.now()).seconds


class MyException(Exception):
    def __init__(self, error):
        self.error = error

    def __str__(self):
        return repr(self.error)


# Converts champion names so they can be used to fetch champion images in a url
async def convert_champion_name(champ_name):
    champ_name = champ_name.lower()
    # These are the special cases that need to be checked
    if "bomb" in champ_name:
        return "bomb-king"
    if "mal" in champ_name:
        return "maldamba"
    if "sha" in champ_name:
        return "sha-lin"
    # else return the name passed in since its already correct
    return champ_name


# Gets a url to the image of champion's name passed in
async def get_champ_image(champ_name):
    champ_name = await convert_champion_name(champ_name)
    url = "https://web2.hirez.com/paladins/champion-icons/" + str(champ_name) + ".jpg"
    return url


# Creates an team image by using champion Icons
async def create_team_image(champ_list, ranks):
    champion_images = []

    while len(champ_list) != 5:
        champ_list.append("?")

    for champ in champ_list:
        if champ != "?" and "Atlas" != champ:  # Temp fix
            champ_url = await get_champ_image(champ)
            response = requests.get(champ_url)
            champion_images.append(Image.open(BytesIO(response.content)))
        else:
            image_size = 512
            base = Image.new('RGB', (image_size, image_size), "black")

            # put text on image
            base_draw = ImageDraw.Draw(base)
            base_draw.text((128, 56), "?", font=ImageFont.truetype("arial", 400))
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

    # box – The crop rectangle, as a (left, upper, right, lower)-tuple.

    # Row 1
    match_image.paste(Image.open(buffer1), (0, 0, (image_size*len(team1)), image_size))

    # Middle row
    match_image.paste(Image.open(middle), (0, image_size, (image_size * len(team1)), image_size+offset))

    # Row 2
    match_image.paste(Image.open(buffer2), (0, image_size + offset, (image_size*len(team1)), image_size*2 + offset))

    # match_image.show()

    # Creates a buffer to store the image in
    final_buffer = BytesIO()

    # Store the pillow image we just created into the buffer with the PNG format
    match_image.save(final_buffer, "png")

    # seek back to the start of the buffer stream
    final_buffer.seek(0)

    return final_buffer


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


# Class of commands that are solo (a.k.a) are not used/related to other functions
class Lang:
    file_name = 'server_ids'
    lan = []

    lang_dict = {}

    @classmethod
    async def check_language(cls, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in cls.lan:
            return cls.lan[guild_id]
        else:  # default
            return "en"


with open(Lang.file_name) as json_f:
    print("Loaded server languages for lang class")
    Lang.lan = json.load(json_f)


file_name = "lang_dict"
# Loads in language dictionary (need encoding option so it does not mess up other languages)
with open(file_name, encoding='utf-8') as json_f:
    print("Loaded language dictionary for conversions.")
    Lang.lang_dict = json.load(json_f)
