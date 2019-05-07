
"""
# Creates a image desks
async def create_deck_image2(player_name, champ_name, deck):
    image_size_x = 256
    image_size_y = 196

    # Main image
    # deck_image = Image.new('RGB', (image_size_x * 5, image_size_x * 2), color=color)

    # Champ icon image
    champ_url = await get_champ_image(champ_name)
    response = requests.get(champ_url)
    champ_icon_image = Image.open(BytesIO(response.content))
    champ_icon_image = champ_icon_image.resize((image_size_x, image_size_x))

    img2 = champ_icon_image.resize((1, 1))
    color = img2.getpixel((0, 0))

    deck_image = Image.new('RGB', (image_size_x * 5, image_size_x * 2), color=color)

    deck_image.paste(champ_icon_image, (0, 0, image_size_x, image_size_x))

    # Loop to add all the cards in
    for i, card in enumerate(deck.cards):
        card_m = str(card).split("(")
        number = str(card_m[1]).split(")")[0]

        card_icon_url = await get_deck_cards_url(card_m[0])
        response = requests.get(card_icon_url)
        card_icon_image = Image.open(BytesIO(response.content))

        # box – The crop rectangle, as a (left, upper, right, lower)- tuple.
        deck_image.paste(card_icon_image, (image_size_x*i, image_size_x,
                                           image_size_x * (i + 1), image_size_x*2-(image_size_x-image_size_y)))

        draw = ImageDraw.Draw(deck_image)
        draw.text((image_size_x * i, image_size_x*2 + 10 - (image_size_x-image_size_y)), str(card),
                  font=ImageFont.truetype("arial", 32))

    # This works, found online
    # img2 = champ_icon_image.resize((1, 1))
    # color = img2.getpixel((0, 0))
    color = (255, 255, 255)

    # Adding in other text on image
    draw = ImageDraw.Draw(deck_image)
    draw.text((image_size_x, 0), str(player_name), color, font=ImageFont.truetype("arial", 64))
    draw.text((image_size_x, 64), str(champ_name), color, font=ImageFont.truetype("arial", 64))
    draw.text((image_size_x, 128), str(deck.deckName), color, font=ImageFont.truetype("arial", 64))

    # Creates a buffer to store the image in
    final_buffer = BytesIO()

    # Store the pillow image we just created into the buffer with the PNG format
    deck_image.save(final_buffer, "png")

    # seek back to the start of the buffer stream
    final_buffer.seek(0)

    return final_buffer
"""
