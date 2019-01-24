import random
import traceback
import asyncio

from discord import Game
from discord.ext.commands import Bot

# Discord Variables
BOT_PREFIX = ("!!", ">>")
client = Bot(command_prefix=BOT_PREFIX)
TOKEN = "NTM3MzQ1ODE3MDcwMTQxNDUw.Dyptmw.zHrf5ozKflMqoBEDDxywOI9T0XA"


# List of Champs by Class
Damage = ["Cassie", "Kinessa", "Drogoz", "Bomb King", "Viktor", "Sha Lin", "Tyra", "Willo", "Lian", "Strix", "Vivian",
          "Dredge", "Imani"]
Flank = ["Skye", "Buck", "Evie", "Androxus", "Maeve", "Lex", "Zhin", "Talus", "Moji", "Koga"]
FrontLine = ["Barik", "Fernado", "Ruckus", "Makoa", "Trovald", "Inara", "Ash", "Terminus", "Khan"]
Support = ["Grohk", "Grover", "Ying", "Mal'Damba", "Seris", "Jenos", "Furia"]


# Picks a random damage champion.
def pick_damage(damages):
    tmp_damage = Damage
    secure_random = random.SystemRandom()
    for damage in damages:
        tmp_damage.remove(damage)
    return secure_random.choice(tmp_damage)


# Picks a random flank champion.
def pick_flank(flanks):
    tmp_flank = Flank
    secure_random = random.SystemRandom()
    for flank in flanks:
        tmp_flank.remove(flank)
    return secure_random.choice(tmp_flank)


# Picks a random tank champion.
def pick_tank(tanks):
    tmp_tanks = FrontLine
    secure_random = random.SystemRandom()
    for tank in tanks:
        tmp_tanks.remove(tank)
    return secure_random.choice(tmp_tanks)


# Picks a random support champion.
def pick_support(healers):
    tmp_healers = Support
    secure_random = random.SystemRandom()
    for healer in healers:
        tmp_healers.remove(healer)
    return secure_random.choice(tmp_healers)


# Picks a random champion from any class.
def pick_random_champ():
    secure_random = random.SystemRandom()
    return secure_random.choice([pick_damage, pick_support, pick_tank, pick_flank])([])


# Uses the random functions about to generate team of random champions
# It will always pick (1 Damage, 1 Flank, 1 Support, and 1 FrontLine, and then one other champion.)
def gen_team():
    team = []
    print("Random Team")
    team.append(pick_damage([]))
    team.append(pick_flank([]))
    team.append(pick_support([]))
    team.append(pick_tank([]))

    fill = pick_random_champ()
    """Keep Generating a random champ until its not one we already have"""
    while fill in team:
        fill = pick_random_champ()

    team.append(fill)

    """Shuffle the team so people get different roles"""
    random.shuffle(team)
    return team


"""End of Python Functions"""


# Calls python function
@client.command(name='damage',
                description="Picks a random damage champion.",
                brief="Picks a random damage champion.",
                aliases=['Damage', 'DAMAGE'],
                pass_context=True)
async def random_damage():
    await  client.say("Your random damage champion is: " + pick_damage([]))


# This code for some reason does not work other discord functions and cause the bot to only respond to these commands
"""
@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    if message.content.startswith('*hello'):
        msg = 'Hello {0.author.mention}'.format(message)
        await client.send_message(message.channel, msg)
    elif message.content.startswith('*team'):
        await client.send_message(message.channel, str(gen_team()))
"""


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    # Status of the bot
    await client.change_presence(game=Game(name="!!help or >>help"))

"""
async def list_servers():
    await client.wait_until_ready()
    while not client.is_closed:
        print("Current servers: ")
        for server in client.servers:
            print(server.name)
        await asyncio.sleep(600)
"""

"""
@client.command()
async def bitcoin():
    url = "Uasdasd"
    responce = requests.get(url)
    value = responce.json()['bpi']['USD']['rate']
    await client.say(value)
"""

#client.loop.create_task(list_servers())

# Must be called after Discord functions
client.run(TOKEN)


"""Main Function"""
"""
def main():
    gen_team()
    print(pick_random_champ())


main()
"""
