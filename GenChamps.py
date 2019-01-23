import random
import discord


# List of Champs by Class
Damage = ["Cassie", "Kinessa", "Drogoz", "Bomb King", "Viktor", "Sha Lin", "Tyra", "Willo", "Lian", "Strix", "Vivian",
          "Dredge", "Imani"]
Flank = ["Skye", "Buck", "Evie", "Androxus", "Maeve", "Lex", "Zhin", "Talus", "Moji", "Koga"]
FrontLine = ["Barik", "Fernado", "Ruckus", "Makoa", "Trovald", "Inara", "Ash", "Terminus", "Khan"]
Support = ["Grohk", "Grover", "Ying", "Mal'Damba", "Seris", "Jenos", "Furia"]


def pick_damage(damages):
    tmp_damage = Damage
    secure_random = random.SystemRandom()
    for damage in damages:
        tmp_damage.remove(damage)
    return secure_random.choice(tmp_damage)


def pick_flank(flanks):
    tmp_flank = Flank
    secure_random = random.SystemRandom()
    for flank in flanks:
        tmp_flank.remove(flank)
    return secure_random.choice(tmp_flank)


def pick_tank(tanks):
    tmp_tanks = FrontLine
    secure_random = random.SystemRandom()
    for tank in tanks:
        tmp_tanks.remove(tank)
    return secure_random.choice(tmp_tanks)


def pick_support(healers):
    tmp_healers = Support
    secure_random = random.SystemRandom()
    for healer in healers:
        tmp_healers.remove(healer)
    return secure_random.choice(tmp_healers)


def pick_random_champ():
    secure_random = random.SystemRandom()
    return secure_random.choice([pick_damage, pick_support, pick_tank, pick_flank])([])


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
    #print(team)
    return team


"""Discord Stuff"""


TOKEN = "NTM3MzQ1ODE3MDcwMTQxNDUw.Dyj6VQ.EoBkzxmsyYrefTeE5HqGRUn-m70"

client = discord.Client()


@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    if message.content.startswith('!hello'):
        msg = 'Hello {0.author.mention}'.format(message)
        await client.send_message(message.channel, msg)
    elif message.content.startswith('!team'):
        await client.send_message(message.channel, str(gen_team()))

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run(TOKEN)



"""Main Function"""
"""
def main():
    gen_team()
    print(pick_random_champ())


main()
"""