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

bot.run("OTI3MzM1NTg3MzY1NjYyNzQx.GNzh8D.aePzrjpX3plQT_eoOaz70-ekM9PqczN9I9yUjY")
