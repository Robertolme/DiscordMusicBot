import discord
from discord.ext import commands

import os

from music import music_cog

bot = commands.Bot(command_prefix='$')


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    pass

bot.add_cog(music_cog(bot))


bot.run("OTI3MzM1NTg3MzY1NjYyNzQx.GmMDUX.oc5b0-TIkFJZcjIqD-Qn5uIoUTcBlVycBMxly8")

#bot.run("OTI3MzM1NTg3MzY1NjYyNzQx.GmMDUX.oc5b0-TIkFJZcjIqD-Qn5uIoUTcBlVycBMxly8")