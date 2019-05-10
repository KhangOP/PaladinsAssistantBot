from PIL import Image, ImageFont, ImageDraw
import requests
from io import BytesIO
from datetime import datetime, timedelta
from pytz import timezone
import json
import textwrap
import time
import os
import re

from concurrent.futures import ThreadPoolExecutor
import asyncio

'''This file servers to provide helper functions that our used in more than one other program.'''


directory = 'user_info'
usage = "usage"
limits = "limits"
current_uses_per_day = 4
card_frames_dir = "icons/card_frames"

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
async def convert_champion_name(champ_name, special=False):
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
async def get_champ_image(champ_name):
    champ_name = await convert_champion_name(champ_name)
    url = "https://web2.hirez.com/paladins/champion-icons/" + str(champ_name) + ".jpg"
    return url


# Gets a url to the image of a champion's name passed in
async def get_deck_cards_url(card_name: str):
    card_name = card_name.lower().replace(" ", "-")
    url = "https://web2.hirez.com/paladins/champion-cards/" + card_name + ".jpg"
    return url


# Creates an team image by using champion Icons
async def create_team_image(champ_list, ranks):
    champion_images = []

    while len(champ_list) != 5:
        champ_list.append("?")

    for champ in champ_list:
        if champ != "?":  # and "Atlas" != champ:  # Temp fix
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
    # start = time.time()
    buffer1 = await create_team_image(team1, ranks1)
    buffer2 = await create_team_image(team2, ranks2)
    middle = await draw_match_vs()
    # end = time.time()
    # print("run1", end - start)

    """
    start = time.time()
    buffer1, buffer2, middle = await asyncio.gather(
        create_team_image(team1, ranks1),
        create_team_image(team2, ranks2),
        draw_match_vs()
    )
    end = time.time()
    print("run2", end - start)
    """

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


async def create_card_image(card_image, champ_info):
    image_size_x = 256
    image_size_y = 196
    x_offset = 28
    y_offset = 48
    champ_name = champ_info[0]
    champ_card_name = champ_info[1]
    champ_card_level = champ_info[2]

    # Load in the Frame image from the web
    response = requests.get("https://web2.hirez.com/paladins/cards/frame-{}.png".format(champ_card_level))
    card_frame = Image.open(BytesIO(response.content))
    frame_x, frame_y = card_frame.size

    # Create the image without any text (just frame and card image)
    image_base = Image.new('RGBA', (frame_x, frame_y), (0, 0, 0, 0))

    # Resizing images that don't match the common image size
    check_x, check_y = card_image.size
    if check_x != image_size_x or check_y != image_size_y:
        card_image = card_image.resize((image_size_x, image_size_y), Image.ANTIALIAS)

    image_base.paste(card_image, (x_offset, y_offset, image_size_x + x_offset, image_size_y + y_offset))
    image_base.paste(card_frame, (0, 0), card_frame)

    # Add in the Card Number
    draw = ImageDraw.Draw(image_base)
    draw.text((30, frame_y-56), champ_card_level, font=ImageFont.truetype("arialbd", 44))

    # Get card data
    english_code = 1
    json_data = requests.get("https://cms.paladins.com/wp-json/wp/v2/champions?slug={}&lang_id={}"
                             .format(await convert_champion_name(champ_name, True), english_code))
    json_data = json_data.json()[0].get("cards")

    cool_down = 0
    desc = "???"
    for card in json_data:
        # print(card.get("card_name_english"), champ_card_name)
        if card.get("card_name_english") == champ_card_name:
            desc = card.get("card_description")

            # Scale of the card
            scale = re.search('=(.+?)\|', desc)
            # Text area of the card we are going to replace
            replacement = re.search('{(.*?)}', desc)

            # Replacing the scaling text with the correct number
            desc = desc.replace('{'+str(replacement.group(1))+'}', str(float(scale.group(1)) * int(champ_card_level)))

            # Removes the extra text at the start in-between [****]
            desc = re.sub("[\[].*?[\]]", '', desc)
            cool_down = card.get("recharge_seconds")

    # Add card name
    draw = ImageDraw.Draw(image_base)
    font = ImageFont.truetype("arialbd", 21)
    text_x, text_y = draw.textsize(champ_card_name, font=font)
    draw.text(((frame_x-text_x)/2, (frame_y-text_y)/2+20), champ_card_name, font=font)

    # Add card text
    draw = ImageDraw.Draw(image_base)
    font = ImageFont.truetype("arial", 18)
    lines = textwrap.wrap(desc, width=26)
    padding = 40
    for line in lines:
        text_x, text_y = draw.textsize(line, font=font)
        draw.text(((frame_x-text_x)/2, (frame_y - text_y) / 2 + padding+20), line, font=font, fill=(64, 64, 64))
        padding += 25

    # Add in cool down if needed
    if cool_down != 0:
        # add in number
        draw = ImageDraw.Draw(image_base)
        draw.text((int(frame_x/2)+2, frame_y - 66), str(cool_down), font=ImageFont.truetype("arial", 30), fill=(64, 64, 64))

        # add in cool down icon
        response = requests.get("https://c-3sux78kvnkay76x24mgskvkjogx2eiax78ykijtx2eius.g00.gamepedia.com/g00/3_c-3vgrgjoty.mgskvkjog.ius_/c-3SUXKVNKAY76x24nzzvyx3ax2fx2fmgskvkjog.iax78ykijt.iusx2fvgrgjoty_mgskvkjogx2flx2fl1x2fIuurjuct_Oiut.vtmx3fbkx78youtx3d53lijk999h1kll086lg16j7kjh186821x26o76i.sgx78qx3dosgmk_$/$/$/$/$")
        cool_down_icon = Image.open(BytesIO(response.content)).convert("RGBA")
        image_base.paste(cool_down_icon, (int(frame_x/2)-20, frame_y - 60), mask=cool_down_icon)



    # Final image saving steps
    # Creates a buffer to store the image in
    final_buffer = BytesIO()

    # Store the pillow image we just created into the buffer with the PNG format
    image_base.save(final_buffer, "png")

    # seek back to the start of the buffer stream
    final_buffer.seek(0)

    return final_buffer


# Creates a image desks
async def create_deck_image(player_name, champ_name, deck):
    image_size_xy = 256

    card_image_x = 314
    card_image_y = 479

    # Champ icon image
    # champ_url = await get_champ_image(champ_name)
    # response = requests.get(champ_url)
    # champ_icon_image = Image.open(BytesIO(response.content))
    # champ_icon_image = champ_icon_image.resize((image_size_xy, image_size_xy))

    # img2 = champ_icon_image.resize((1, 1))
    # color = img2.getpixel((0, 0))

    # Main image
    color = (0, 0, 0, 0)
    deck_image = Image.new('RGBA', (1570, 800), color=color)

    # deck_image.paste(champ_icon_image, (0, 0, image_size_xy, image_size_xy))
    response = requests.get("https://web2.hirez.com/paladins/champion-headers/{}.png"
                            .format(await convert_champion_name(champ_name)))
    champ_background = Image.open(BytesIO(response.content))
    champ_background = champ_background.resize((1570, 800), Image.ANTIALIAS)
    deck_image.paste(champ_background, (0, 0))

    # Loop to add all the cards in
    for i, card in enumerate(deck.cards):
        card_m = str(card).split("(")
        number = str(card_m[1]).split(")")[0]
        info = [champ_name, card_m[0].strip(), number]

        card_icon_url = await get_deck_cards_url(card_m[0].strip())
        response = requests.get(card_icon_url)
        try:
            card_icon_image = Image.open(BytesIO(response.content))
        except OSError:
            card_icon_image = Image.open("icons/temp_card_art.png")

        card_icon = await create_card_image(card_icon_image, info)

        # box – The crop rectangle, as a (left, upper, right, lower)- tuple.
        # deck_image.paste(Image.open(card_icon), (card_image_x * i, image_size_xy, card_image_x * (i + 1),
        #                                         image_size_xy + card_image_y), champ_background)
        card_icon = Image.open(card_icon)
        deck_image.paste(card_icon, (card_image_x * i, 800-card_image_y), card_icon)

        # draw = ImageDraw.Draw(deck_image)
        # draw.text((image_size_x, image_size_x + image_size_y*i), str(card), font=ImageFont.truetype("arial", 48))

    # This works, found online
    # img2 = champ_icon_image.resize((1, 1))
    # color = img2.getpixel((0, 0))
    color = (255, 255, 255)

    # Adding in other text on image
    draw = ImageDraw.Draw(deck_image)
    draw.text((0, 0), str(player_name), color, font=ImageFont.truetype("arial", 64))
    draw.text((0, 64), str(champ_name), color, font=ImageFont.truetype("arial", 64))
    draw.text((0, 128), str(deck.deckName), color, font=ImageFont.truetype("arial", 64))

    # Creates a buffer to store the image in
    final_buffer = BytesIO()

    # Store the pillow image we just created into the buffer with the PNG format
    deck_image.save(final_buffer, "png")

    # seek back to the start of the buffer stream
    final_buffer.seek(0)

    return final_buffer


# Creates a image desks
async def create_deck_image_old(player_name, champ_name, deck):
    image_size_xy = 256

    card_image_x = 314
    card_image_y = 479

    # Champ icon image
    champ_url = await get_champ_image(champ_name)
    response = requests.get(champ_url)
    champ_icon_image = Image.open(BytesIO(response.content))
    champ_icon_image = champ_icon_image.resize((image_size_xy, image_size_xy))

    # img2 = champ_icon_image.resize((1, 1))
    # color = img2.getpixel((0, 0))

    # Main image
    color = (0, 0, 0, 0)
    deck_image = Image.new('RGBA', (card_image_x * 5, card_image_y*2), color=color)

    deck_image.paste(champ_icon_image, (0, 0, image_size_xy, image_size_xy))

    # Loop to add all the cards in
    for i, card in enumerate(deck.cards):
        card_m = str(card).split("(")
        number = str(card_m[1]).split(")")[0]
        info = [champ_name, card_m[0].strip(), number]

        card_icon_url = await get_deck_cards_url(card_m[0].strip())
        response = requests.get(card_icon_url)
        try:
            card_icon_image = Image.open(BytesIO(response.content))
        except OSError:
            card_icon_image = Image.open("icons/temp_card_art.png")

        card_icon = await create_card_image(card_icon_image, info)

        # box – The crop rectangle, as a (left, upper, right, lower)- tuple.
        deck_image.paste(Image.open(card_icon), (card_image_x * i, image_size_xy, card_image_x * (i + 1),
                                                 image_size_xy + card_image_y))

        # draw = ImageDraw.Draw(deck_image)
        # draw.text((image_size_x, image_size_x + image_size_y*i), str(card), font=ImageFont.truetype("arial", 48))

    # This works, found online
    # img2 = champ_icon_image.resize((1, 1))
    # color = img2.getpixel((0, 0))
    color = (255, 255, 255)

    # Adding in other text on image
    draw = ImageDraw.Draw(deck_image)
    draw.text((image_size_xy, 0), str(player_name), color, font=ImageFont.truetype("arial", 64))
    draw.text((image_size_xy, 64), str(champ_name), color, font=ImageFont.truetype("arial", 64))
    draw.text((image_size_xy, 128), str(deck.deckName), color, font=ImageFont.truetype("arial", 64))

    # Creates a buffer to store the image in
    final_buffer = BytesIO()

    # Store the pillow image we just created into the buffer with the PNG format
    deck_image.save(final_buffer, "png")

    # seek back to the start of the buffer stream
    final_buffer.seek(0)

    return final_buffer


# Creates a match image based on the two teams champions #ToDo Finish implementation in the future
async def create_history_image(team1, team2, t1_data, t2_data):
    image_size = 512
    offset = 5
    history_image = Image.new('RGB', (image_size*10, image_size*10))
    for i, (champ, champ2) in enumerate(zip(team1, team2)):
        champ_url = await get_champ_image(champ)
        response = requests.get(champ_url)
        champ_image = Image.open(BytesIO(response.content))
        history_image.paste(champ_image, (0, image_size*i, image_size, image_size*(i+1)))

        # Second team
        champ_url = await get_champ_image(champ2)
        response = requests.get(champ_url)
        champ_image = Image.open(BytesIO(response.content))
        history_image.paste(champ_image, (0, image_size * (i + offset), image_size, image_size * (i + 1 + offset)))
    # history_image.show()

    # Creates a buffer to store the image in
    final_buffer = BytesIO()

    # Store the pillow image we just created into the buffer with the PNG format
    history_image.save(final_buffer, "png")

    # seek back to the start of the buffer stream
    final_buffer.seek(0)

    return final_buffer


# Class of commands that are solo (a.k.a) are not used/related to other functions
class Lang:
    file_name = 'languages/server_configs'
    lan = {}

    @classmethod
    async def check_language(cls, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in cls.lan:
            return cls.lan[guild_id]["lang"]
        else:  # default
            return "en"


with open(Lang.file_name) as json_f:
    print("Loaded server languages for lang class")
    Lang.lan = json.load(json_f)
