

# Get the image of champion's name passed in
async def get_champ_image(champ_name):
    champ_name = champ_name.lower()
    # These are special cases that need to ge checked
    if "bomb" in champ_name:
        return "https://web2.hirez.com/paladins/champion-icons/bomb-king.jpg"
    if "mal" in champ_name:
        return "https://web2.hirez.com/paladins/champion-icons/maldamba.jpg"
    if "sha" in champ_name:
        return "https://web2.hirez.com/paladins/champion-icons/sha-lin.jpg"

    url = "https://web2.hirez.com/paladins/champion-icons/" + str(champ_name) + ".jpg"
    return url
