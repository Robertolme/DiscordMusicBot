import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import re
from typing import Optional, Deque, Dict
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

class MusicConfig:
    def __init__(self):
        self.max_queue_size = 50
        self.max_song_length = 600  # 10 minutos en segundos
        self.inactivity_timeout = 300  # 5 minutos
        self.max_retries = 3
        self.default_volume = 0.5
        self.allowed_formats = ['bestaudio/best']

class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = MusicConfig()
        self.is_playing: bool = False
        self.nightcore_active = False
        self.music_queue: Deque[Dict[str, str]] = deque()
        self.voice_channel: Optional[discord.VoiceChannel] = None
        self.vc: Optional[discord.VoiceClient] = None
        self.volume = self.config.default_volume
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        self.stats = {
            'songs_played': 0,
            'total_queue_time': 0.0,
            'errors': 0
        }

        self.YDL_OPTIONS = {
            'format': self.config.allowed_formats[0],
            'noplaylist': True,
            'quiet': True,
            'socket_timeout': 10,
            'default_search': 'auto',
        }

        self.FFMPEG_OPTIONS_DEFAULT = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin',
            'options': '-vn -b:a 128k -bufsize 1024k', 
        }

        self.FFMPEG_OPTIONS_NIGHTCORE = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin',
            'options': '-vn -af "atempo=1.2, asetrate=44100*1.2"'
        }

        self.FFMPEG_OPTIONS = self.FFMPEG_OPTIONS_DEFAULT

    @lru_cache(maxsize=100)
    def descargar(self, query: str) -> Optional[Dict[str, str]]:
        """Descarga información de la canción con caché LRU."""
        try:
            with youtube_dl.YoutubeDL(self.YDL_OPTIONS) as ydl:
                info = ydl.extract_info(query, download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                
                if info.get('duration', 0) > self.config.max_song_length:
                    raise ValueError("Canción demasiado larga")
                
                return {
                    'source': info['url'],
                    'title': info['title'],
                    'duration': info.get('duration', 0)
                }
        except Exception as e:
            print(f"Error en descarga: {e}")
            return None

    async def descargar_async(self, query: str) -> Optional[Dict[str, str]]:
        """Ejecuta la descarga en un thread separado."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, lambda: self.descargar(query))

    async def reproducir(self, ctx: commands.Context, retries: int = None):
        """Maneja la reproducción con reintentos y manejo de errores."""
        retries = retries or self.config.max_retries
        
        try:
            if not self.music_queue:
                self.is_playing = False
                await self.start_inactivity_timer()
                return

            if self.vc and (self.vc.is_playing() or self.vc.is_paused()):
                return

            self.is_playing = True
            cancion = self.music_queue.popleft()

            if self.vc is None or not self.vc.is_connected():
                self.vc = await self.voice_channel.connect(reconnect=True, timeout=30)

            self.vc.stop()
            source = discord.FFmpegPCMAudio(cancion['source'], **self.FFMPEG_OPTIONS)
            source = discord.PCMVolumeTransformer(source, self.volume)

            await ctx.send(f"Reproduciendo: **{cancion['title']}**")
            self.stats['songs_played'] += 1
            self.stats['total_queue_time'] += cancion['duration']

            self.vc.play(source, after=lambda e: (
                self.bot.loop.create_task(self.handle_playback_error(e, ctx)) if e else
                self.bot.loop.create_task(self.reproducir(ctx))
            ))

        except discord.ClientException as e:
            print(f"ClientException: {e}")
            if retries > 0:
                await asyncio.sleep(1)
                await self.reproducir(ctx, retries-1)
        except Exception as e:
            print(f"Error en reproducción: {e}")
            await ctx.send("Error al reproducir la canción")
            await self.cleanup()

    async def handle_playback_error(self, error: Exception, ctx: commands.Context):
        """Maneja errores de reproducción."""
        if error:
            print(f"Error en playback: {error}")
            self.stats['errors'] += 1
            await ctx.send("Error al reproducir la canción, intentando siguiente...")
        await self.reproducir(ctx)

    async def start_inactivity_timer(self):
        """Inicia el temporizador de inactividad."""
        await asyncio.sleep(self.config.inactivity_timeout)
        if not self.is_playing and self.vc:
            await self.cleanup()

    async def cleanup(self):
        """Limpia todos los recursos."""
        if self.vc and self.vc.is_connected():
            await self.vc.disconnect()
        self.vc = None
        self.music_queue.clear()
        self.is_playing = False
        self.descargar.cache_clear()

    def in_voice_channel():
        """Decorador para verificar canal de voz."""
        async def predicate(ctx):
            if not ctx.author.voice:
                await ctx.send("Debes estar en un canal de voz!")
                return False
            return True
        return commands.check(predicate)

    @commands.command(name="play", help="Reproduce una canción o añade a tu cola")
    @in_voice_channel()
    async def play(self, ctx: commands.Context, *, query: str):
        """Maneja el comando de reproducción con validaciones."""
        self.voice_channel = ctx.author.voice.channel

        if len(self.music_queue) >= self.config.max_queue_size:
            await ctx.send("Tu esta Cola llena, intente más tarde")
            return

        if not self.is_youtube_url(query):
            query = f"ytsearch:{query}"

        cancion = await self.descargar_async(query)
        if not cancion:
            await ctx.send("La ptm no seas monky, inserta una cancion valida")
            return

        self.music_queue.append(cancion)
        await ctx.send(f"({len(self.music_queue)} **{cancion['title']}** Añadido a tu cola ")

        if not self.is_playing:
            await self.reproducir(ctx)

    @commands.command(name="skip", help="Salta la canción actual")
    @in_voice_channel()
    async def skip(self, ctx: commands.Context):
        """Salta la canción actual."""
        if self.vc and self.vc.is_playing():
            self.vc.stop()
            await ctx.send(" Canción saltada")
            await self.reproducir(ctx)

    @commands.command(name="queue", help="Muestra la cola de reproducción")
    async def queue(self, ctx: commands.Context):
        """Muestra la cola actual."""
        if not self.music_queue:
            await ctx.send("Tu Cola vacía")
            return

        queue_list = "\n".join([f"{i+1}. {song['title']}" for i, song in enumerate(self.music_queue)])
        await ctx.send(f"**Cola actual ({len(self.music_queue)})**\n{queue_list}")

    @commands.command(name="playnext", help="Añade una canción al principio de la cola")
    @in_voice_channel()
    async def play_next(self, ctx: commands.Context, *, query: str):
        """Añade canción con prioridad."""
        cancion = await self.descargar_async(query)
        if cancion:
            self.music_queue.appendleft(cancion)
            await ctx.send(f"Canción añadida como próxima: **{cancion['title']}**")

    @commands.command(name="volume", help="Ajusta el volumen (0-100)")
    async def volume(self, ctx: commands.Context, volume: int):
        """Control de volumen."""
        if 0 <= volume <= 100:
            self.volume = volume / 100
            if self.vc and self.vc.source:
                self.vc.source.volume = self.volume
            await ctx.send(f" Volumen ajustado a {volume}%")
        else:
            await ctx.send(" Volumen debe estar entre 0 y 100")

    @commands.command(name="stop", help="Detiene y limpia todo")
    @in_voice_channel()
    async def stop(self, ctx: commands.Context):
        """Detiene completamente el bot."""
        await self.cleanup()
        await ctx.send("Reproducción detenida y cola limpiada")

    @staticmethod
    def is_youtube_url(query: str) -> bool:
        """Valida URLs de YouTube."""
        patterns = [
            r'(https?://)?(www\.)?youtube\.com/watch\?v=',
            r'(https?://)?(www\.)?youtu\.be/'
        ]
        return any(re.search(pattern, query) for pattern in patterns)

    def get_ffmpeg_options(self):
        if self.nightcore_active:
            self.FFMPEG_OPTIONS = self.FFMPEG_OPTIONS_NIGHTCORE
        else:
            self.FFMPEG_OPTIONS = self.FFMPEG_OPTIONS_DEFAULTs
    @commands.command()
    async def nightcore(self, ctx):
        self.nightcore_active = not self.nightcore_active
        status = "activado" if self.nightcore_active else "desactivado"
        self.get_ffmpeg_options()
        await ctx.send(f"✨ Efecto Nightcore {status}")