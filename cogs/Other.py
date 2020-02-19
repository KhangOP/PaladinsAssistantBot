from discord.ext import commands
import json
import os


# Class handles server configs. Allows a server owner to change the language or prefix of the bot in a server
class OtherCog(commands.Cog, name="Other Cog"):
    """OtherCog"""

    dashes = "----------------------------------------"
    directory = 'user_info'

    def __init__(self, bot):
        self.bot = bot

    # Print how many times a person has used each command
    @commands.command(name='usage', aliases=["użycie"])
    async def usage(self, ctx):
        user_commands = await self.get_store_commands(ctx.author.id)
        len(user_commands)
        message = "Commands used by {}\n{}\n".format(ctx.author, self.dashes)

        # Data to plot
        labels = []
        data = []
        i = 1

        for command, usage in user_commands.items():
            message += "{}. {:9} {}\n".format(str(i), str(command), str(usage))
            labels.append(command)
            data.append(usage)
            i += 1

        await ctx.send('```md\n' + message + '```')

    # Gets ths command uses of a person based on their discord_id
    async def get_store_commands(self, discord_id):
        discord_id = str(discord_id)
        found = False
        for filename in os.listdir(self.directory):
            if filename == discord_id:
                found = True
                break
            else:
                continue

        # if we found the player in the player dir
        if found:
            with open(self.directory + "/" + discord_id) as personal_json:
                user_info = json.load(personal_json)
                return user_info[self.usage]
        # we did not find the user in the player dir so we need to make fun of them
        else:
            return "Lol, you trying to call this command without ever using the bot."

    # Stores Player's IGN for the bot to use
    @commands.command(name='store', pass_context=True, ignore_extra=False,
                      aliases=["zapisz", "Zapisz", "Store", 'salva'])
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def store_player_name(self, ctx, player_ign):
        with open("player_discord_ids") as json_f:
            player_discord_ids = json.load(json_f)

        player_discord_ids.update({str(ctx.author.id): player_ign})  # update dict

        # need to update the file now
        print("Stored a IGN in conversion dictionary: " + player_ign)
        with open("player_discord_ids", 'w') as json_f:
            json.dump(player_discord_ids, json_f)
        await ctx.send("Your Paladins In-Game-name is now stored as `" + player_ign +
                       "`. You can now use the keyword `me` instead of typing out your name")


# Add this class to the cog list
def setup(bot):
    bot.add_cog(OtherCog(bot))
