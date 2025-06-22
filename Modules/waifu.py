import discord
from discord.ext import commands
from openai import OpenAI
from Modules.music import MusicCog
import re
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="env/config.env")  # Carga variables de .env automáticamente

API = os.getenv("DEEP")

client = OpenAI(api_key=API, base_url="https://api.deepseek.com")

class WaifuConfig:
    def __init__(self):
        self.max_tok = 600
        self.n_resp = 1
        self.creatividad = 0.8
        self.pesonal = "tsundere" #tsundere Kuudere

class WaifuCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.config = WaifuConfig()
        self.music = MusicCog(bot)

    @commands.command(name="message", help="Dile algo a la waifu")
    async def message(self, ctx: commands.Context, *, query: str):
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": f"Eres una waifu bot de un servidor de discord con una personalidad {self.config.pesonal}"},
                {"role": "user", "content": query},
            ],
            stream=False,
            max_tokens=self.config.max_tok,
            temperature=self.config.creatividad,
            n=self.config.n_resp,
        )

        await ctx.send(response.choices[0].message.content)

    @commands.command(name="random", help="La waifu te elije")
    async def random(self, ctx, *, tema: str = ""):
        promp = f"Recomienda 10 caciones random de {tema}, escribe solo el nombre de las canciones y su artista, numeradas y separadas por un salto de linea. Evita el uso de comillas o carateres extraños"
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Eres una waifu bot kawai que recomienda musica"},
                {"role": "user", "content": promp},
            ],
            stream=False,
            max_tokens=600,
            temperature=0.7,
            n=1,
        )
        recomendaciones = response.choices[0].message.content
        titulos = re.findall(r"\d+\.\s*(.+)", recomendaciones)
        for i in titulos:
            cancion = str(i)
            await ctx.invoke(self.bot.get_command("play"), query=i)
        await ctx.send(recomendaciones)
    
