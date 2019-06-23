import discord
from discord.ext import commands
import random
import json

import my_utils as helper


class RandomCog(commands.Cog, name="Random Commands"):
    """RandomCog"""

    def __init__(self, bot):
        self.bot = bot
        self.load_lang()

    # List of Champs by Class
    DAMAGES = ["Cassie", "Kinessa", "Drogoz", "Bomb King", "Viktor", "Sha Lin", "Tyra", "Willo", "Lian", "Strix",
               "Vivian", "Dredge", "Imani"]
    DAMAGE_CMD = ["damage", "napastnik", "dano"]
    FLANKS = ["Skye", "Buck", "Evie", "Androxus", "Maeve", "Lex", "Zhin", "Talus", "Moji", "Koga"]
    FLANK_CMD = ["flank", "skrzydłowy", "flanco"]
    FRONTLINES = ["Barik", "Fernando", "Ruckus", "Makoa", "Torvald", "Inara", "Ash", "Terminus", "Khan", "Atlas"]
    FRONTLINE_CMD = ["tank", "frontline", "obrońca", "tanque"]
    SUPPORTS = ["Grohk", "Grover", "Ying", "Mal Damba", "Seris", "Jenos", "Furia", "Pip"]
    SUPPORT_CMD = ["healer", "support", "wsparcie", "suporte"]
    CHAMP_CMD = ["champ", "czempion", "campeão"]
    TEAM_CMD = ["team", "drużyna", "time", "comp"]
    MAP_CMD = ["map", "mapa"]
    # Map Names
    MAPS = ["Frog Isle", "Jaguar Falls", "Serpent Beach", "Frozen Guard", "Ice Mines", "Fish Market", "Timber Mill",
            "Stone Keep", "Brightmarsh", "Splitstone Quarry", "Ascension Peak", "Warder's Gate", "Shattered Desert",
            "Bazaar"]

    lang_dict = {}
    file_name = "languages/random_lang_dict"

    def load_lang(self):
        # Loads in language dictionary (need encoding option so it does not mess up other languages)
        with open(self.file_name, encoding='utf-8') as json_f:
            print("Loaded random command language dictionary.")
            self.lang_dict = json.load(json_f)

    async def pick_random_champion(self):
        secure_random = random.SystemRandom()
        class_type = secure_random.choice([self.DAMAGES, self.FLANKS, self.SUPPORTS, self.FRONTLINES])
        champ = secure_random.choice(class_type)
        return champ

    async def gen_team(self):
        sr = random.SystemRandom()
        team = [sr.choice(self.DAMAGES), sr.choice(self.FLANKS), sr.choice(self.SUPPORTS), sr.choice(self.FRONTLINES)]

        fill = await self.pick_random_champion()
        """Keep Generating a random champ until its not one we already have"""
        while fill in team:
            fill = await self.pick_random_champion()

        team.append(fill)

        """Shuffle the team so people get different roles"""
        for x in range(random.randint(1, 5)):  # Shuffle a team a random amount of times (1-5)
            random.shuffle(team)

        team_string = "\n"
        for champ in team:
            team_string += champ + "\n"
        return team_string

    # Calls different random functions based on input
    @commands.command(name='rand', aliases=["random", "losuj"], ignore_extra=False)
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def rand(self, ctx, command):
        await helper.store_commands(ctx.author.id, "random")
        lang = await helper.Lang.check_language(ctx=ctx)
        command = str(command).lower()
        embed = discord.Embed(
            colour=discord.colour.Color.dark_teal()
        )

        secure_random = random.SystemRandom()

        if command in self.DAMAGE_CMD:
            champ = secure_random.choice(self.DAMAGES)
            embed.add_field(name=self.lang_dict["random_damage"][lang], value=champ)
            embed.set_thumbnail(url=await helper.get_champ_image(champ))
            # await client.say(embed=embed)
            await ctx.send(embed=embed)
        elif command in self.FLANK_CMD:
            champ = secure_random.choice(self.FLANKS)
            embed.add_field(name=self.lang_dict["random_flank"][lang], value=champ)
            embed.set_thumbnail(url=await helper.get_champ_image(champ))
            await ctx.send(embed=embed)
        elif command in self.SUPPORT_CMD:
            champ = secure_random.choice(self.SUPPORTS)
            embed.add_field(name=self.lang_dict["random_healer"][lang], value=champ)
            embed.set_thumbnail(url=await helper.get_champ_image(champ))
            await ctx.send(embed=embed)
        elif command in self.FRONTLINE_CMD:
            champ = secure_random.choice(self.FRONTLINES)
            embed.add_field(name=self.lang_dict["random_tank"][lang], value=champ)
            embed.set_thumbnail(url=await helper.get_champ_image(champ))
            await ctx.send(embed=embed)
        elif command in self.CHAMP_CMD:
            champ = await self.pick_random_champion()
            embed.add_field(name=self.lang_dict["random_champ"][lang], value=champ)
            embed.set_thumbnail(url=await helper.get_champ_image(champ))
            await ctx.send(embed=embed)
        elif command in self.TEAM_CMD:
            async with ctx.channel.typing():
                team = await self.gen_team()
                buffer = await helper.create_team_image(list(filter(None, team.splitlines())), [])
                file = discord.File(filename="Team.png", fp=buffer)
                await ctx.send("{}\n```css\n{}```".format(self.lang_dict["random_team"][lang], team), file=file)
        elif command in self.MAP_CMD:
            map_name = secure_random.choice(self.MAPS)
            embed.add_field(name=self.lang_dict["random_map"][lang], value=map_name)
            map_name = map_name.lower().replace(" ", "_")
            map_url = "https://raw.githubusercontent.com/EthanHicks1/PaladinsAssistantBot/master/icons/maps/{}.png".\
                format(map_name)
            embed.set_image(url=map_url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(self.lang_dict["random_invalid"][lang])


# Add this class to the cog list
def setup(bot):
    bot.add_cog(RandomCog(bot))
