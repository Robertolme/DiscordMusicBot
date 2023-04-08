import discord
from discord.ext import commands
import os

from music import music_cog


bot = commands.Bot(command_prefix='$',intents = discord.Intents.all())

@bot.event
async def on_ready():
    print('Entrando al servidor como {0.user}'.format(bot))
    await bot.add_cog(music_cog(bot))
    pass

bot.run("TOKEN")
