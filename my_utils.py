from datetime import datetime
from pytz import timezone

'''This file servers to provide helper functions that our used in more than one other program.'''


# Est Time zone for logging function calls
async def get_est_time():
    # using just timezone 'EST' does not include daylight savings
    return datetime.now(timezone('US/Eastern')).strftime("%H:%M:%S %m/%d/%Y")


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


class MyException(Exception):
    def __init__(self, error):
        self.error = error

    def __str__(self):
        return repr(self.error)
