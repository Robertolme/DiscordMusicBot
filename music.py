import discord
from discord.ext import commands
from discord.utils import get
import os

import yt_dlp as youtube_dl

class music_cog(commands.Cog):
	def __init__(self, botr):
		self.bot = botr
		self.is_playing = False
		self.music_info = [] #variable donde se almacenara la informacion del video
		self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
		self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
		self.voice_channel = ""
		self.vc = ""

	def descargar(self, item):
		try:
			ydl = youtube_dl.YoutubeDL(self.YDL_OPTIONS)
			info = ydl.extract_info("ytsearch:%s" % item ,download=False)['entries'][0]
		except Exception:
			return False
		return {'source': info['url'], 'title': info['title']}

	@commands.command(name="play", help="play")
	async def p(self, ctx, *args):
		query = " ".join(args)
		self.voice_channel = ctx.author.voice.channel

		if self.voice_channel is None:
			await ctx.send("No estas conectado a ningun canal de voz")
		else: 
			cancion = self.descargar(query)
			if(cancion == False):
				await ctx.send("No se pudo descargar la canción. Formato incorrecto pruebe con otra palabra clave. Esto podría deberse a una lista de reproducción o un formato de transmisión en vivo.")
			else:
				await ctx.send("Cancion agregada a tu cola")
				self.music_info.append(cancion)

				if self.is_playing == False: 
					await self.reproducir(ctx)

	async def reproducir(self, ctx):
		if len(self.music_info) != 0:
			self.is_playing = True

			m_url = self.music_info[0]['source'] 

			if self.vc == "" or not self.vc.is_connected() or self.vc == None:
				self.vc = await self.voice_channel.connect()
			#else:
			#	await self.vc.move_to(self.voice_channel.connect())

			await ctx.send("Reproduciendo :" + self.music_info[0]['title'])

			self.music_info.pop(0)

			self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
		else: 
			self.is_playing = False

	def play_next(self,ctx):
		if len(self.music_info) != 0:
			self.is_playing = True
			m_url = self.music_info[0]['source']
			self.music_info.pop(0)
			self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
		else:
			self.is_playing = False

	@commands.command(name="skip", help="skip")
	async def skip(self,ctx):
		self.vc.stop()
		if self.vc != "" and self.vc:
			self.play_next(ctx)

	@commands.command(name="desconectar",help="Desconectar bot")
	async def dc(self, ctx):
		await self.vc.disconnect()

	@commands.command(name="next",help="lista")
	async def lst(self,ctx):
		res = ""
		for i in range(0, len(self.music_info)):
			res += f"{i+1}.{self.music_info[i]['title']} \n"

		if res != "":
			await ctx.send(res)
		else:
			await ctx.send("No hay canciones en tu cola")

	@commands.command(name="link",help="link")
	async def lk(self,ctx,*args):
		query = " ".join(args)
		cancion = self.descargar(query)
		await ctx.send(cancion['source'])

	@commands.command(name="playlist",help="agergar lista")
	async def lis(self,ctx,*args):
		query = " ".join(args)
		await os.system("python3 -m yt_dlp --get-filename -o \"%(playlist_title)s - %(title)s - %(id)s\" https://www.youtube.com/playlist?list=PLhESAgWGwV_G4BSOpZaycYE55ioNAkEsA > lista.txt")
		datos = []
		with open("lista.txt") as fname:
			lineas = fname.readlines()
			for linea in lineas:
				datos.append(linea.strip('\n'))
		print(datos)
		# youtube-dl -i --get-filename --skip-download https://www.youtube.com/playlist?list=PLm9l7EEbJuhyDYNuItj3sG8h3xAZbjIxr
		# youtube-dl --get-filename -o "%(playlist_title)s - %(title)s - %(id)s"  











