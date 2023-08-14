import discord
from discord.ext import commands
from discord.utils import get
import os
import yt_dlp as youtube_dl
from discord import Button, ButtonStyle
import json

class MusicCog(commands.Cog,discord.ui.View):
    def __init__(self, bot):
        self.bot = bot
        self.is_playing = False
        self.music_info = []  # variable donde se almacenará la información del video
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                                'options': '-vn'}
        self.voice_channel = None
        self.vc = None
        #self.canciones_reproducidas = self.cargar_registro()

    def descargar(self, item):
        try:
            ydl = youtube_dl.YoutubeDL(self.YDL_OPTIONS)
            info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
            return {'source': info['url'], 'title': info['title']}
        except Exception as e:
            print("Error al descargar la canción:", e)
            return False

    @commands.command(name="play", help="play")
    async def play(self, ctx, *args, send_message=True):
        query = " ".join(args)
        self.voice_channel = ctx.author.voice.channel

        if self.voice_channel is None:
            await ctx.send("No estás conectado a ningún canal de voz")
        else:
            cancion = self.descargar(query)
            if cancion is False:
                await ctx.send(
                    "No se pudo descargar la canción. Formato incorrecto, pruebe con otra palabra clave. Esto podría "
                    "deberse a una lista de reproducción o un formato de transmisión en vivo."
                )
            else:
                if send_message:
                    await ctx.send("Canción agregada a tu cola")
                
                self.music_info.append(cancion)


                if not self.is_playing:
                    await self.reproducir(ctx)

    async def reproducir(self, ctx):
        if self.music_info:
            self.is_playing = True

            m_url = self.music_info[0]['source']
            name = self.music_info[0]['title']

            #self.canciones_reproducidas.append(name)
            #self.guardar_registro()

            if self.vc is None or not self.vc.is_connected():
                self.vc = await self.voice_channel.connect()

            await ctx.send("Reproduciendo: " + self.music_info[0]['title'])

            self.music_info.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
        else:
            self.is_playing = False

    def play_next(self, ctx):
        if self.music_info:
            self.is_playing = True
            m_url = self.music_info[0]['source']
            name = self.music_info[0]['title']
            #self.canciones_reproducidas.append(name)
            #self.guardar_registro()
            self.music_info.pop(0)
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
        else:
            self.is_playing = False

    @commands.command(name="skip", help="skip")
    async def skip(self, ctx):
        if self.vc and self.vc.is_playing():
            self.vc.stop()
            self.play_next(ctx)

    @commands.command(name="disconnect", help="Desconectar bot")
    async def disconnect(self, ctx):
        if self.vc and self.vc.is_connected():
            await self.vc.disconnect()

    @commands.command(name="next", help="lista")
    async def queue(self, ctx):
        if self.music_info:
            res = ""
            for i, song in enumerate(self.music_info, start=1):
                res += f"{i}. {song['title']}\n"
            await ctx.send(res)
        else:
            await ctx.send("No hay canciones en tu cola")

    @commands.command(name="link", help="link")
    async def get_link(self, ctx, *args):
        query = " ".join(args)
        cancion = self.descargar(query)
        await ctx.send(cancion['source'] if cancion else "No se encontró el enlace.")

    def obtener_nombres_mix_youtube(self, url_mix):
        try:
            # Configura las opciones de youtube_dl para obtener solo el título de los videos
            ydl_opts = {
                'ignoreerrors': True,
                'quiet': True,
                'extract_flat': 'in_playlist',
                'skip_download': True,
                'format': 'best'
            }

            # Crea un objeto youtube_dl con la URL del mix de YouTube
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url_mix, download=False)

            # Extrae los nombres de los videos de la información obtenida
            video_names = [entry['title'] for entry in info['entries']]

            # Devuelve la lista de nombres de los videos
            return video_names

        except Exception as e:
            print("Ocurrió un error al obtener los nombres de los videos:", e)
            return []

    @commands.command(name="mix", help="Reproduce una playlist de YouTube")
    async def play_mix(self, ctx, *args):
        query = ""
        limit = 20

        for i, arg in enumerate(args):
            if arg == "-n" and i + 1 < len(args):
                limit = int(args[i + 1])
            else:
                query += arg + " "

        query = query.strip()
        lista_music = self.obtener_nombres_mix_youtube(query)

        for index, title in enumerate(lista_music):
            if index < limit:
                await self.play(ctx, title, send_message=index == 0)
            else:
                break

    @commands.command(name="stop", help="Detiene y borra la lista actual de reproducción")
    async def stop(self, ctx, *args):
        if self.vc and self.vc.is_playing():
            self.vc.stop()
        self.music_info = []
