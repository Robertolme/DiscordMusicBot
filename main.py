import discord
from discord.ext import commands
import os
import openai 

from music import MusicCog

bot = commands.Bot(command_prefix='$',intents = discord.Intents.all())

@bot.event
async def on_ready():
    print('Entrando al servidor como {0.user}'.format(bot))
    await bot.add_cog(MusicCog(bot))
    pass

bot.run("OTI3MzM1NTg3MzY1NjYyNzQx.G74UH_.OeglFxnHVw8bf45ue8uos7jdDemwDzL1rIhTqg")

# api 
