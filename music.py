import discord
from discord.ext import commands
from discord.utils import get

from youtube_dl import YoutubeDL

class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
        self.is_playing = False

        # 2d array contiene [song, channel]
        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        self.vc = ""

        self.i = -1

        self.voice_channel = ""

     #busca en youtube
    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try: 
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
            except Exception: 
                return False

        return {'source': info['formats'][0]['url'], 'title': info['title']}

    def play_next(self):
        if len(self.music_queue) > (self.i+1):
            self.is_playing = True

            self.i += 1
            m_url = self.music_queue[self.i][0]['source']      
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False
            self.music_queue = ""
            self.i = -1

    # comprobación de bucle infinito 
    async def play_music(self):
        if len(self.music_queue) > (self.i+1):
            self.is_playing = True

            self.i += 1
            m_url = self.music_queue[self.i][0]['source']

            
            #intente conectarse al canal de voz si aún no está conectado

            if self.vc == "" or not self.vc.is_connected() or self.vc == None:
                self.vc = await self.music_queue[0][1].connect()
            else:
                await self.vc.move_to(self.music_queue[0][1])
            
            print(self.music_queue)
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False
            self.music_queue = ""
            self.i = -1



    @commands.command(name="play", help="play")
    async def p(self, ctx, *args):
        query = " ".join(args)
        
        self.voice_channel = ctx.author.voice.channel
        if self.voice_channel is None:
            await ctx.send("No estas conectado a un canal de voz")
        else:
            song = self.search_yt(query)
            if type(song) == type(True):
                await ctx.send("No se pudo descargar la canción. Formato incorrecto pruebe con otra palabra clave. Esto podría deberse a una lista de reproducción o un formato de transmisión en vivo.")
            else:
                await ctx.send("Cancion agregada a tu cola")
                self.music_queue.append([song,self.voice_channel])
                
                print(self.music_queue)
                
                if self.is_playing == False:
                    await self.play_music()

    @commands.command(name="lista", help="Muestra la canciones en cola")
    async def q(self, ctx):
        retval = ""
        for i in range(0, len(self.music_queue)):
            retval += i + ". " +self.music_queue[i][0]['title'] + "\n"
        print(retval)
        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send("No hay caniones tu cola")

    @commands.command(name="skip", help="Skip")
    async def skip(self, ctx):
        self.vc.stop()
        if self.vc != "" and self.vc:
            self.play_next()
            
    @commands.command(name="desconectar", help="Desconectar bot")
    async def dc(self, ctx):
        await self.vc.disconnect()




    