from datetime import datetime, timedelta
from pytz import timezone
import json
import os


"""
start = time.time()
"the code you want to placeholder stays here"
end = time.time()
print(end - start)
"""


"""This file servers to provide helper functions that our used in more than one other program."""
directory = 'user_info'
usage = "usage"
limits = "limits"
current_uses_per_day = 4
card_frames_dir = "icons/card_frames"

command_list = ['last', 'stats', 'random', 'current', 'history', 'deck', 'match', 'top']
command_limits = ['current']


# Logs how many times someone uses a command
# if used == -1 then don't worry about tracking limits
async def store_commands(discord_id, command_name, used=-1):
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
        try:
            user_info[usage][command_name] += 1
        except KeyError:  # Add keys that are missing
            user_info[usage][command_name] = 1

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


# Est Time zone for logging function calls
async def get_est_time():
    # using just timezone 'EST' does not include daylight savings
    return datetime.now(timezone('US/Eastern')).strftime("%H:%M:%S %m/%d/%Y")


# Gets minutes left in the hour
async def get_second_until_hour():
    minutes_left_in_hour = 60 - datetime.now().minute   # Get minutes left until the next hour
    minutes_left_in_hour = minutes_left_in_hour - 5     # (5 minutes before the hour)
    if minutes_left_in_hour < 0:
        return 0
    return minutes_left_in_hour


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


# Converts champion names to include spacing in the name if needed
async def convert_champion_name_normal(champ_name: str):
    champ_name = champ_name.title()
    # These are the special cases that need to be checked
    if "Bomb" in champ_name:
        return "Bomb King"
    if "Mal" in champ_name:
        return "Mal Damba"
    if "Sha" in champ_name:
        return "Sha Lin"
    # else return the name passed in since it's already correct
    return champ_name


# Converts champion names so they can be used to fetch champion images in a url or from local computer
async def convert_champion_name_image(champ_name, special=False):
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
    champ_name = await convert_champion_name_image(champ_name)
    url = "https://raw.githubusercontent.com/EthanHicks1/PaladinsAssistantBot/master/icons/champ_icons/{}.png"\
        .format(champ_name)
    return url


# adds in whitespace by adding in spaces separated by the the (zero-width-space)[\u200b] character to trick Discord
async def force_whitespace(string, max_length):
    padded_string = string
    length = len(padded_string)

    if length % 2 != 0:
        padded_string += " "

    max_length = (max_length - length) * 2 + length

    while len(padded_string) <= max_length:
        padded_string += "\u200b "

    return padded_string
