import discord
from discord.ext import commands

from ignora.token import token

import os

from music import music_cog

bot = commands.Bot(command_prefix='$')


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    pass

bot.add_cog(music_cog(bot))


bot.run(token())

