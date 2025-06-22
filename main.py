import discord
from discord.ext import commands
import os
bot = commands.Bot(command_prefix='$',intents = discord.Intents.all())

from Modules.music import MusicCog
from Modules.waifu import WaifuCog

config_file = "env/config.env"
TOKEN = None

if os.path.exists(config_file):
    with open(config_file, "r") as file:
        for line in file:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                if key == "BOT_TOKEN":
                    TOKEN = value
                else:	
                	print("No token")
else:
	print(f"No se encontró el archivo de configuración: {config_file}")



@bot.event
async def on_ready():
    print('Entrando al servidor como {0.user}'.format(bot))
    await bot.add_cog(MusicCog(bot))
    await bot.add_cog(WaifuCog(bot))
    pass

def main():    
	bot.run(TOKEN)

if __name__ == '__main__':
	main()

# api 
