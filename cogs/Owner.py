from discord.ext import commands
from psutil import Process
from os import getpid


# Hold commands that only the bot owner can use
class OwnerCog(commands.Cog, name="Bot Owner Commands"):
    """OwnerCog"""

    dashes = "----------------------------------------"

    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.command(name='check_bot', aliases=["bot_check"])
    async def check_bot(self, ctx):
        with open("log_file.csv", 'r') as r_log_file:
            lines = r_log_file.read().splitlines()
            servers, n1, old_errors, num_cmd, old_api_calls, old_date = lines[-1].split(',')

        bot_memory = f'{round(Process(getpid()).memory_info().rss/1024/1024, 2)} MB'

        ss = "1. [Server count:]({})\n2. [Help Server Members:]({})\n3. [Fatal Errors:]({})\n4. " \
             "[Commands Used:]({})\n5. [API Calls Used:]({})\n6. [Date:]({})\n7. [Memory Usage:]({})" \
            .format(servers, n1.strip(), old_errors.strip(), num_cmd.strip(), old_api_calls.strip(), old_date.strip(),
                    bot_memory.strip())
        ss_f = '```md\n' + self.dashes + '\n' + ss + '```'
        await ctx.send(ss_f)


# Add this class to the cog list
def setup(bot):
    bot.add_cog(OwnerCog(bot))
