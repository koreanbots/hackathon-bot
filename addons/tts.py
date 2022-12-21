import dico
import dico_command
import dico_extsource

from typing import Optional, Dict
from re import compile, sub

from dico_command.utils import search

from modules.tts import generate_tts


EMOJI = compile(r"<a?:(.+?):\d{18,20}>")
URL = compile(
    r"[http|https\:\/\/]?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.[a-zA-Z][a-zA-Z0-9\.\&\/\?\:@\-_=#]*"
)


class TTS(dico_command.Addon):
    tts_audio: dico_extsource.Mixer
    tts_channel_id: Optional[dico.Snowflake]
    filters: Dict[str, str]

    async def addon_check(self, ctx: dico_command.Context):
        return bool(search(ctx.member.roles, name="TEAM"))

    def on_load(self):
        self.tts_audio = dico_extsource.Mixer()
        self.tts_channel_id = None
        self.filters = {"atempo": "1.0"}

    @dico_command.command("tts")
    async def tts(self, ctx: dico_command.Context):
        if self.tts_channel_id:
            self.tts_channel_id = None
            voice = self.bot.get_voice_client(ctx.guild)
            await voice.close()
            await ctx.reply("✅ TTS 기능을 껐어요.")
        else:
            if self.bot.get_voice_client(ctx.guild):
                return await ctx.send("❌ TTS 기능을 사용하기 위해서는 기존 보이스 플레이어를 제거해야 합니다.")
            voice = await self.bot.connect_voice(
                ctx.guild.id, ctx.author.voice_state.channel_id
            )
            await voice.play(self.tts_audio, lock_audio=True)
            self.tts_channel_id = ctx.channel_id
            await ctx.reply(f"✅ TTS 기능을 <#{ctx.channel_id}>에서 켰어요!")

    @tts.subcommand("volume")
    async def tts_volume(self, ctx: dico_command.Context, volume: int = None):
        if volume is None:
            return await ctx.reply(
                f"{'🔊' if self.tts_audio.volume >= 0.5 else '🔉'} 현재 TTS 볼륨은 `{self.tts_audio.volume*100}`% 입니다."
            )
        self.tts_audio.volume = volume / 100
        await ctx.reply(f"✅ TTS 볼륨을 `{volume}`%로 설정했어요.")

    @tts.subcommand("speed")
    async def tts_speed(self, ctx: dico_command.Context, speed: float = None):
        if speed > 2 or speed < 0.5:
            return await ctx.reply("❌ 잘못된 설정값입니다. 0.5 ~ 2.0 사이만 가능합니다.")
        self.filters["atempo"] = str(speed)
        await ctx.reply(f"✅ 배속을 `{speed}`로 설정했습니다.")

    @dico_command.on("message_create")
    async def on_tts_message(self, message: dico.Message):
        if (
            message.author.bot
            or not self.tts_channel_id
            or message.channel_id != self.tts_channel_id
            or await self.bot.verify_prefix(message)
        ):
            return
        msg = message.content

        msg = msg.replace("ㅋ", "크").replace("ㅎ", "흐").replace("ㄷ", "덜")

        if message.mentions:
            for mention in message.mentions:
                msg = msg.replace(f"<@!{mention.user.id}>", f"{mention}")
                msg = msg.replace(f"<@{mention.user.id}>", f"{mention}")

        msg = sub(EMOJI, r"\1", msg)

        msg = sub(URL, "", msg)

        tts = await generate_tts(msg, loop=self.bot.loop)
        if tts:
            audio = dico_extsource.PyAVSource(tts, AVOption={"mode": "r"})
            audio.filter = self.filters
            self.tts_audio.addTrack(audio)


def load(bot):
    bot.load_addons(TTS)


def unload(bot):
    bot.unload_addons(TTS)
