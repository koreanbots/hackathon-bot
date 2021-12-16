import random
import asyncio
import datetime

import dico
import dico_command
import dico_extsource
import dico_interaction

from typing import List, Tuple, Optional, Any, Union, Dict

from dico.utils import rgb
from dico.voice import VoiceClient

from modules.utils import parse_second


class MusicData:
    def __init__(self):
        self.queue: List[dico_extsource.YTDLSource] = []
        self.queue_added: asyncio.Event = asyncio.Event()
        self.requires_audio: bool = False
        self.volume: float = 1.0
        self.queue_task_running: Optional[asyncio.Task] = None
        self.latest_channel_id: Optional[dico.Snowflake] = None
        self.loop: bool = False
        self.shuffle: bool = False

    @property
    def queue_task_unavailable(self) -> bool:
        return not self.queue_task_running or (
            self.queue_task_running.cancelled() or self.queue_task_running.done()
        )


class Music(dico_command.Addon):
    music_data: Dict[dico.Snowflake, MusicData]

    def on_load(self):
        self.music_data = {}

    def voice_check(
        self,
        ctx: dico_command.Context,
        *,
        check_connected: bool = False,
        check_playing: bool = False,
        check_paused: bool = False,
    ) -> Tuple[int, Optional[str]]:
        state = ctx.author.voice_state

        if check_playing and check_paused:
            return 5, "❌ 잘못된 설정입니다."

        if not state or not state.channel_id or state.guild_id != ctx.guild_id:
            return 1, "❌ 먼저 음성 채널에 들어와주세요."

        voice = self.bot.get_voice_client(ctx.guild_id)

        if check_connected and voice is None:
            return 2, "❌ 먼저 음악을 재생해주세요."

        if check_playing and voice.paused:
            return 3, "❌ 음악이 재생중이 아닙니다. 먼저 음악을 재생해주세요."

        if check_paused and not voice.paused:
            return 4, "❌ 음악이 재생중입니다. 먼저 음악을 일시정지해주세요."

        return 0, None

    async def queue_task(self, guild_id: dico.Snowflake):
        while True:
            voice = self.bot.get_voice_client(guild_id)
            if not voice or voice.ws.destroyed:
                break
            audio_loaded = voice.audio
            await voice.wait_audio_done()
            music_data = self.music_data[guild_id]
            if music_data.queue or music_data.loop:
                if music_data.loop:
                    audio_loaded = dico_extsource.YTDLSource(
                        audio_loaded.Data
                    )  # let's just hope that URL is still valid
                    # await audio_loaded.seek(0)
                audio = (
                    audio_loaded
                    if music_data.loop
                    else music_data.queue.pop(
                        random.randint(0, len(music_data.queue) - 1)
                        if music_data.shuffle
                        else 0
                    )
                )
                embed = self.build_embed(audio, title="재생 시작")
                audio.volume = music_data.volume
                await voice.play(audio)
                await self.bot.create_message(audio.invoked_at, embed=embed)
            else:
                try:
                    music_data.requires_audio = True
                    await self.bot.create_message(
                        music_data.latest_channel_id,
                        "ℹ 대기열이 비었습니다. 5분 안에 음악이 추가되지 않으면 플레이어가 종료됩니다.",
                    )
                    await asyncio.wait_for(
                        music_data.queue_added.wait(),
                        timeout=60 * 5,
                        loop=self.bot.loop,
                    )
                except asyncio.TimeoutError:
                    await voice.close()
                    await self.bot.create_message(
                        music_data.latest_channel_id, "ℹ 플레이어를 종료합니다."
                    )
                    music_data.queue_task_running = None
                    music_data.queue = []
                    break
                finally:
                    music_data.requires_audio = False
                    if music_data.queue_added.is_set():
                        music_data.queue_added.clear()

    @staticmethod
    def build_embed(
        audio: dico_extsource.YTDLSource, title: Optional[str] = None
    ) -> dico.Embed:
        requester = audio.requester
        embed = dico.Embed(
            title=title,
            description=f"[{audio.title}]({audio.webpage_url})",
            color=0x0FD439,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_thumbnail(url=audio.thumbnail)
        embed.set_author(name=audio.uploader, url=audio.channel_url)
        embed.set_footer(text=f"요청자: {requester}", icon_url=requester.user.avatar_url())
        return embed

    @dico_command.command("play", aliases=["queue", "p", "q", "pl"])
    async def play(self, ctx: dico_command.Context, *, query: str):
        code, text = self.voice_check(ctx)
        if code:
            return await ctx.reply(text)
        voice = self.bot.get_voice_client(ctx.guild)
        if not voice:
            state = ctx.author.voice_state
            voice = await self.bot.connect_voice(ctx.guild, state.channel)
            self.music_data[ctx.guild_id] = MusicData()
        music_data = self.music_data[ctx.guild_id]
        await ctx.create_reaction("<a:loading:868755640909201448>")
        audio = await dico_extsource.YTDLSource.create(query)
        audio.Data["requester"] = ctx.member
        audio.Data["invoked_at"] = ctx.channel_id
        music_data.latest_channel_id = ctx.channel_id
        embed = self.build_embed(audio)
        if music_data.queue_task_unavailable:
            embed.title = "재생 시작"
            await voice.play(audio)
        else:
            embed.title = "대기열 추가"
            music_data.queue.append(audio)
            if music_data.requires_audio and not music_data.queue_added.is_set():
                music_data.queue_added.set()
        await ctx.delete_reaction("<a:loading:868755640909201448>")
        await ctx.create_reaction("✅")
        await ctx.reply(embed=embed)
        if not music_data.queue_task_running:
            music_data.queue_task_running = self.bot.loop.create_task(
                self.queue_task(ctx.guild_id)
            )

    @dico_command.command("volume", aliases=["vol", "v"])
    async def volume(self, ctx, volume: int = None):
        code, text = self.voice_check(ctx, check_connected=True)
        if code:
            return await ctx.reply(text)
        voice = self.bot.get_voice_client(ctx.guild)
        music_data = self.music_data[ctx.guild_id]
        if volume is None:
            return await ctx.reply(
                f"{'🔊' if voice.audio.volume >= 0.5 else '🔉'} 현재 음악 볼륨은 `{voice.audio.volume*100}`% 입니다."
            )
        if volume < 0 or volume > 100:
            return await ctx.reply("❌ 볼륨은 0~100 사이의 숫자만 가능합니다.")
        voice.audio.volume = volume / 100
        music_data.volume = volume / 100
        await ctx.reply(f"✅ 음악 볼륨을 `{volume}`%로 설정했습니다.")

    @dico_command.command("skip", aliases=["s"])
    async def skip(self, ctx: dico_command.Context, index: int = 0):
        code, text = self.voice_check(ctx, check_connected=True, check_playing=True)
        if code:
            return await ctx.reply(text)
        music_data = self.music_data[ctx.guild_id]
        if abs(index) > len(music_data.queue):
            return await ctx.reply("❌ 잘못된 값입니다.")
        voice = self.bot.get_voice_client(ctx.guild)
        if index == 0:
            text = "현재 재생중인 "
            await voice.stop()
        else:
            if index < 0:
                text = f"{-index}개의 "
                for _ in range(-index):
                    music_data.queue.pop(0)
            else:
                text = f"{index}번쩨 "
                music_data.queue.pop(index - 1)
        await ctx.reply(f"✅ {text}음악을 스킵했습니다.")

    @dico_command.command("stop")
    async def stop(self, ctx: dico_command.Context):
        code, text = self.voice_check(ctx, check_connected=True)
        if code:
            return await ctx.reply(text)
        voice = self.bot.get_voice_client(ctx.guild)
        music_data = self.music_data[ctx.guild_id]
        music_data.queue = []
        if not music_data.queue_task_unavailable:
            music_data.queue_task_running.cancel()
        music_data.queue_task_running = None
        await voice.close()
        await ctx.reply("✅ 모든 대기열을 지우고 음악을 정지했습니다.")

    @dico_command.command("pause", aliases=["ps"])
    async def pause(self, ctx: dico_command.Context):
        code, text = self.voice_check(ctx, check_connected=True, check_playing=True)
        if code:
            return await ctx.reply(text)
        voice = self.bot.get_voice_client(ctx.guild)
        voice.pause()
        await ctx.reply("✅ 음악을 일시정지했습니다.")

    @dico_command.command("resume", aliases=["rs"])
    async def resume(self, ctx: dico_command.Context):
        code, text = self.voice_check(ctx, check_connected=True, check_paused=True)
        if code:
            return await ctx.reply(text)
        voice = self.bot.get_voice_client(ctx.guild)
        voice.resume()
        await ctx.reply("✅ 음악을 다시 재생합니다.")

    @dico_command.command("loop", aliases=["l"])
    async def loop(self, ctx: dico_command.Context):
        code, text = self.voice_check(ctx, check_connected=True)
        if code:
            return await ctx.reply(text)
        music_data = self.music_data[ctx.guild_id]
        music_data.loop = not music_data.loop
        await ctx.reply(f"✅ 현재 재생중인 음악을 반복{'합니다' if music_data.loop else ' 해제합니다'}.")

    @dico_command.command("shuffle", aliases=["sf"])
    async def shuffle(self, ctx: dico_command.Context):
        code, text = self.voice_check(ctx, check_connected=True)
        if code:
            return await ctx.reply(text)
        music_data = self.music_data[ctx.guild_id]
        music_data.shuffle = not music_data.shuffle
        await ctx.reply(f"✅ 대기열 셔플을 설정{'합니다' if music_data.loop else ' 해제합니다'}.")

    @staticmethod
    def create_index_bar(length: float, timestamp: float):
        percent = timestamp / length
        pos = round(percent * 30)
        base = ["=" for _ in range(30)]
        base[pos if pos <= 29 else -1] = "🔴"
        vid = parse_second(round(length))
        cpos = parse_second(round(timestamp))
        return f"**{''.join(base)}** [`{cpos}`/`{vid}`]"

    def create_np_embed(
        self, np_audio: dico_extsource.YTDLSource, voice: VoiceClient
    ) -> dico.Embed:
        requester = np_audio.requester
        bar = self.create_index_bar(np_audio.duration, np_audio.position)
        music_data = self.music_data[voice.ws.guild_id]
        extra_scope = ""
        if music_data.loop:
            extra_scope += " | 🔂"
        if music_data.shuffle:
            extra_scope += " | 🔀"
        volume = np_audio.volume
        status = (
            f"{'⏸' if voice.paused else '▶'}{extra_scope} | {'🔊' if volume >= 0.5 else '🔉'} `{volume * 100}`% "
            f"| 📁 `{len(music_data.queue)}`개 대기중"
        )
        np_embed = dico.Embed(
            title=np_audio.title,
            description=f"{bar}\n{status}",
            color=0x1483BB,
            url=np_audio.webpage_url,
            timestamp=datetime.datetime.utcnow(),
        )
        np_embed.set_thumbnail(url=np_audio.thumbnail)
        np_embed.set_author(name=np_audio.uploader, url=np_audio.channel_url)
        np_embed.set_footer(
            text=f"요청자: {requester}", icon_url=requester.user.avatar_url()
        )
        return np_embed

    def create_queue_embed(
        self, guild_id: dico.Snowflake, index: Optional[int] = None
    ) -> Union[dico.Embed, List[dico.Embed]]:
        music_data = self.music_data[guild_id]
        queue = music_data.queue.copy()  # in case of modification
        texts = [
            f"#{i+1} [`{a.title}`]({a.webpage_url}) - {a.requester.mention}"
            for i, a in enumerate(queue)
        ]
        base_embed = dico.Embed(
            title=f"대기열 - 총 {len(queue)}개",
            color=rgb(225, 225, 225),
            timestamp=datetime.datetime.utcnow(),
        )
        resp = []
        em = base_embed.copy()
        em.description = texts[0]
        max_page = len(queue) // 10 + 1
        em.set_footer(text=f"페이지 1/{max_page}")
        for i, x in enumerate(texts):
            if i == 0:
                continue
            if i % 10 == 0:
                resp.append(em)
                em = base_embed.copy()
                em.description = x
                em.set_footer(text=f"페이지 {i // 10 + 1}/{max_page}")
                continue
            em.description += f"\n{x}"
        resp.append(em)
        if index is None:
            return resp
        else:
            return resp[index]

    @staticmethod
    def create_buttons(enable_np: bool, enable_queue: bool, cid: Any):
        if enable_np and enable_queue:
            raise ValueError(
                "enable_np and enable_queue must be different or both False"
            )
        button_np = dico.Button(
            style=dico.ButtonStyles.SUCCESS,
            emoji="⏯",
            custom_id=f"nowplaying{cid}",
            disabled=not enable_np,
        )
        button_queue = dico.Button(
            style=dico.ButtonStyles.PRIMARY,
            emoji="📁",
            custom_id=f"queue{cid}",
            disabled=not enable_queue,
        )
        button_prev = dico.Button(
            style=dico.ButtonStyles.SECONDARY,
            emoji="⬅",
            custom_id=f"ppage{cid}",
            disabled=not enable_np,
        )
        button_next = dico.Button(
            style=dico.ButtonStyles.SECONDARY,
            emoji="➡",
            custom_id=f"npage{cid}",
            disabled=not enable_np,
        )
        return dico.ActionRow(button_np, button_queue, button_prev, button_next)

    def create_check(self, ctx: dico_command.Context):
        def wrap(inter_ctx: dico_interaction.InteractionContext):
            if int(inter_ctx.author) != int(ctx.author):
                self.bot.loop.create_task(
                    inter_ctx.send("이 버튼은 사용하실 수 없습니다.", ephemeral=True)
                )
            return inter_ctx.data.custom_id.endswith(str(ctx.id)) and int(
                inter_ctx.author
            ) == int(ctx.author)

        return wrap

    @dico_command.command(
        "list", aliases=["ql", "queuelist", "player", "nowplaying", "np"]
    )
    async def queue_list(self, ctx: dico_command.Context):
        voice = self.bot.get_voice_client(ctx.guild_id)
        np_audio = voice.audio
        if not voice or not np_audio:
            return await ctx.reply("❌ 음악을 재생하고 있지 않습니다.")
        music_data = self.music_data[ctx.guild_id]
        if not music_data.queue:
            return await ctx.reply(embed=self.create_np_embed(np_audio, voice))
        np_page = True
        index = 0
        max_index = len(music_data.queue) // 10 + 1
        msg = await ctx.reply("<a:loading:868755640909201448> 잠시만 기다려주세요...")
        while True:
            embed = (
                self.create_np_embed(np_audio, voice)
                if np_page
                else self.create_queue_embed(ctx.guild_id, index)
            )
            await msg.edit(
                content=None,
                embed=embed,
                components=[self.create_buttons(not np_page, np_page, ctx.id)],
            )
            try:
                interaction = await self.bot.interaction.wait_interaction(
                    timeout=30, check=self.create_check(ctx)
                )
                await interaction.send(update_message=True)
            except asyncio.TimeoutError:
                return await msg.edit(
                    components=[self.create_buttons(False, False, ctx.id)]
                )
            if interaction.data.custom_id.startswith("nowplaying"):
                np_page = True
            elif interaction.data.custom_id.startswith("queue"):
                np_page = False
            elif interaction.data.custom_id.startswith("npage"):
                index += 1
                if index >= max_index:
                    index = 0
            elif interaction.data.custom_id.startswith("ppage"):
                index -= 1
                if index < 0:
                    index = max_index - 1


def load(bot):
    bot.load_addons(Music)


def unload(bot):
    bot.unload_addons(Music)
