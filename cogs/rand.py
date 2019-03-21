import discord
from discord.ext import commands
import random

import my_utils as helper


class RandomCog(commands.Cog, name="Random Commands"):
    """RandomCog"""

    def __init__(self, bot):
        self.bot = bot

    # List of Champs by Class
    DAMAGES = ["Cassie", "Kinessa", "Drogoz", "Bomb King", "Viktor", "Sha Lin", "Tyra", "Willo", "Lian", "Strix",
               "Vivian",
               "Dredge", "Imani"]
    FLANKS = ["Skye", "Buck", "Evie", "Androxus", "Maeve", "Lex", "Zhin", "Talus", "Moji", "Koga"]
    FRONTLINES = ["Barik", "Fernando", "Ruckus", "Makoa", "Torvald", "Inara", "Ash", "Terminus", "Khan"]
    SUPPORTS = ["Grohk", "Grover", "Ying", "Mal Damba", "Seris", "Jenos", "Furia"]

    # Map Names
    MAPS = ["Frog Isle", "Jaguar Falls", "Serpent Beach", "Frozen Guard", "Ice Mines", "Ice Mines", "Fish Market",
            "Timber Mill", "Stone Keep", "Brightmarsh", "Splitstone Quarry", "Ascension Peak", "Warder's Gate"]

    def pick_random_champion(self):
        secure_random = random.SystemRandom()
        class_type = secure_random.choice([self.DAMAGES, self.FLANKS, self.SUPPORTS, self.FRONTLINES])
        champ = secure_random.choice(class_type)
        return champ

    async def gen_team(self):
        sr = random.SystemRandom()
        team = [sr.choice(self.DAMAGES), sr.choice(self.FLANKS), sr.choice(self.SUPPORTS), sr.choice(self.FRONTLINES)]

        fill = self.pick_random_champion()
        """Keep Generating a random champ until its not one we already have"""
        while fill in team:
            fill = self.pick_random_champion()

        team.append(fill)

        """Shuffle the team so people get different roles"""
        for x in range(random.randint(1, 5)):  # Shuffle a team a random amount of times (1-5)
            random.shuffle(team)

        team_string = "\n"
        for champ in team:
            team_string += champ + "\n"
        return team_string

    # Calls different random functions based on input
    @commands.command(name='rand', aliases=['random', 'r'])
    async def rand(self, ctx, command):
        command = str(command).lower()
        embed = discord.Embed(
            colour=discord.colour.Color.dark_teal()
        )

        secure_random = random.SystemRandom()

        if command == "damage":
            champ = secure_random.choice(self.DAMAGES)
            embed.add_field(name="Your random Damage champion is: ", value=champ)
            embed.set_thumbnail(url=await helper.get_champ_image(champ))
            # await client.say(embed=embed)
            await ctx.send(embed=embed)
        elif command == "flank":
            champ = secure_random.choice(self.FLANKS)
            embed.add_field(name="Your random Flank champion is: ", value=champ)
            embed.set_thumbnail(url=await helper.get_champ_image(champ))
            await ctx.send(embed=embed)
        elif command == "healer":
            champ = secure_random.choice(self.SUPPORTS)
            embed.add_field(name="Your random Support/Healer champion is: ", value=champ)
            embed.set_thumbnail(url=await helper.get_champ_image(champ))
            await ctx.send(embed=embed)
        elif command == "tank":
            champ = secure_random.choice(self.FRONTLINES)
            embed.add_field(name="Your random FrontLine/Tank champion is: ", value=champ)
            embed.set_thumbnail(url=await helper.get_champ_image(champ))
            await ctx.send(embed=embed)
        elif command == "champ":
            champ = self.pick_random_champion()
            embed.add_field(name="Your random champion is: ", value=champ)
            embed.set_thumbnail(url=await helper.get_champ_image(champ))
            await ctx.send(embed=embed)
        elif command == "team":
            async with ctx.channel.typing():
                team = await self.gen_team()
                buffer = await helper.create_team_image(list(filter(None, team.splitlines())))
                file = discord.File(filename="Team.png", fp=buffer)
                await ctx.send("Your random team is: \n" + "```css\n" + team + "```", file=file)
        elif command == "map":
            await  ctx.send("Your random map is: " + "```css\n" + secure_random.choice(self.MAPS) + "```")
        else:
            await ctx.send("Invalid command. For the random command please choose from one following options: "
                           "damage, flank, healer, tank, champ, team, or map. "
                           "\n For example: `>>random damage` will pick a random damage champion")


# Add this class to the cog list
def setup(bot):
    bot.add_cog(RandomCog(bot))
