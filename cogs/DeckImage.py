from discord.ext import commands
from discord import Embed, colour, File

from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
import json
import textwrap
import re


class Decks(commands.Cog, name="Decks Command"):
    """Decks Cog"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='deck', pass_context=True,
                      aliases=["Deck", "decks", "Decks", "talia", "Talia", 'baralho', 'baralhos'], ignore_extra=False)
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

        await store_commands(ctx.author.id, "deck")
        async with ctx.channel.typing():
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

            champ_name = await self.convert_champion_name(champ_name)

            lang_num = await self.convert_language(lang)
            player_decks = self.bot.paladinsAPI.getPlayerLoadouts(player_id, language=lang_num)

            if player_decks is None:
                await ctx.send("A Hi-Rez endpoint is down meaning this command won't work. "
                               "Please don't try again for a while and give Hi-Rez a few hours to get the "
                               "endpoint online again.")
                return None

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
                message = "Decks for " + player_name + "'s " + champ_name + ":\n" + self.bot.DASHES + "\n"
                for i, deck in enumerate(deck_list, start=1):
                    message += str(i) + '. ' + deck + "\n"

                await ctx.send("```md\n" + message + "```")
            else:
                buffer = await self.create_deck_image(player_name, champ_name, deck, lang=lang)
                file = File(filename="Deck.png", fp=buffer)
                await ctx.send("```Enjoy the beautiful image below.```", file=file)

    # Creates a image desks
    @classmethod
    async def create_deck_image(cls, player_name, champ_name, deck, lang):
        card_image_x = 314
        card_image_y = 479

        # Main image
        color = (0, 0, 0, 0)
        deck_image = Image.new('RGBA', (1570, 800), color=color)

        champ_name = await convert_champion_name(champ_name)
        try:
            champ_background = Image.open("icons/champ_headers/{}.png".format(champ_name)).convert('RGBA')
        except FileNotFoundError:
            champ_background = Image.open("icons/maps/test_maps.png").convert('RGBA')
        champ_background = champ_background.resize((1570, 800), Image.ANTIALIAS)
        deck_image.paste(champ_background, (0, 0))

        # Loop to add all the cards in
        for i, card in enumerate(deck.cards):
            card_m = str(card).split("(")
            number = str(card_m[1]).split(")")[0]
            info = [card_m[0].strip(), number]

            # open data file
            if "mal" in champ_name.lower():
                champ_name = "mal-damba"

            # Opens the json data that relates to the specific champion
            try:
                file_name = "icons/champ_card_desc_lang/{}.json".format(champ_name)
                # file_name = "icons/champ_card_desc/{}.json".format(champ_name)    # Just English
                with open(file_name, encoding='utf-8') as json_f:
                    json_data = json.load(json_f)
            except (IndexError, json.decoder.JSONDecodeError, FileNotFoundError):
                json_data = {}

            # Opens the image of the card
            try:
                if 'mal' in champ_name:
                    champ_name = "Mal'Damba"
                try:
                    en_card_name = json_data[lang][card_m[0].strip()]["card_name_en"]
                    en_card_name = en_card_name.strip().lower().replace(" ", "-").replace("'", "")
                except KeyError:
                    en_card_name = "Not implemented yet."

                card_icon_image = Image.open("icons/champ_cards/{}/{}.png".format(champ_name, en_card_name))
            except FileNotFoundError:
                card_icon_image = Image.open("icons/temp_card_art.png")

            card_icon = await cls.create_card_image(card_icon_image, info, json_data, lang=lang)

            card_icon = Image.open(card_icon)
            deck_image.paste(card_icon, (card_image_x * i, 800 - card_image_y), card_icon)

        color = (255, 255, 255)

        if "mal" in champ_name:
            champ_name = "Mal'Damba"
        else:
            champ_name = champ_name.upper()

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

    @classmethod
    async def create_card_image(cls, card_image, champ_info, json_data, lang):
        image_size_x = 256
        image_size_y = 196
        x_offset = 28
        y_offset = 48
        champ_card_name = champ_info[0]
        champ_card_level = champ_info[1]

        # Load in the Frame image from the web
        # response = requests.get("https://web2.hirez.com/paladins/cards/frame-{}.png".format(champ_card_level))
        # card_frame = Image.open(BytesIO(response.content))
        card_frame = Image.open("../icons/card_frames/{}.png".format(champ_card_level))
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
        draw.text((30, frame_y - 56), champ_card_level, font=ImageFont.truetype("arialbd", 44))

        try:
            desc = json_data[lang][champ_card_name]["card_desc"]
            cool_down = json_data[lang][champ_card_name]["card_cd"]

            # todo --- find all the cards that don't have the word scale in them and see if they follow the same format
            # some cards don't have the word "scale" in them because cool-down scales.
            if "scale" not in desc:
                pass
            else:
                # Scale of the card
                scale = re.search('=(.+?)\|', desc)
                scale = float(scale.group(1)) * int(champ_card_level)
                # Text area of the card we are going to replace
                replacement = re.search('{(.*?)}', desc)

                # Replacing the scaling text with the correct number
                # desc = desc.replace('{'+str(replacement.group(1))+'}', str(float(scale.group(1))
                # * int(champ_card_level)))
                desc = desc.replace('{' + str(replacement.group(1)) + '}', str(round(scale, 1)))

                # Removes the extra text at the start in-between [****]
                desc = re.sub("[\[].*?[\]]", '', desc)
        except KeyError:
            desc = "Card information missing from bot data."
            cool_down = 0
        except AttributeError:
            desc = "Couldn't find card description for some reason. Please report this."
            cool_down = 0

        # Add card name
        draw = ImageDraw.Draw(image_base)
        font = ImageFont.truetype("arialbd", 21)
        text_x, text_y = draw.textsize(champ_card_name, font=font)
        draw.text(((frame_x - text_x) / 2, (frame_y - text_y) / 2 + 20), champ_card_name, font=font)

        # Add card text
        draw = ImageDraw.Draw(image_base)
        font = ImageFont.truetype("arial", 18)
        lines = textwrap.wrap(desc, width=26)
        padding = 40
        for line in lines:
            text_x, text_y = draw.textsize(line, font=font)
            draw.text(((frame_x - text_x) / 2, (frame_y - text_y) / 2 + padding + 20), line, font=font,
                      fill=(64, 64, 64))
            padding += 25

        # Add in cool down if needed
        if cool_down != 0:
            # add in number
            draw = ImageDraw.Draw(image_base)
            draw.text((int(frame_x / 2) + 2, frame_y - 66), str(cool_down), font=ImageFont.truetype("arial", 30),
                      fill=(64, 64, 64))

            cool_down_icon = Image.open("../icons/cool_down_icon.png")
            image_base.paste(cool_down_icon, (int(frame_x / 2) - 20, frame_y - 60), mask=cool_down_icon)

        # Final image saving steps
        # Creates a buffer to store the image in
        final_buffer = BytesIO()

        # Store the pillow image we just created into the buffer with the PNG format
        image_base.save(final_buffer, "png")

        # seek back to the start of the buffer stream
        final_buffer.seek(0)

        return final_buffer


# Add this class to the cog list
def setup(bot):
    bot.add_cog(Decks(bot))
