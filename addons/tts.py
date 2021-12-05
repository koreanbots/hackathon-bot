import dico
import dico_command
import dico_extsource
import dico_interaction

from typing import Optional

from modules.tts import generate_tts


class TTS(dico_command.Addon):
    tts_audio: dico_extsource.Mixer
    tts_channel_id: Optional[dico.Snowflake]

    def on_load(self):
        self.tts_audio = dico_extsource.Mixer()
        self.tts_channel_id = None

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
            voice = await self.bot.connect_voice(ctx.guild.id, ctx.author.voice_state.channel_id)
            await voice.play(self.tts_audio, lock_audio=True)
            self.tts_channel_id = ctx.channel_id
            await ctx.reply(f"✅ TTS 기능을 <#{ctx.channel_id}>에서 켰어요!")

    @tts.subcommand("volume")
    async def tts_volume(self, ctx: dico_command.Context, volume: int = None):
        volume = int(volume) if volume else None  # TODO: auto conversion in dico-command
        if volume is None:
            return await ctx.reply(f"🔈 현재 TTS 볼륨은 `{self.tts_audio.volume*100}`% 입니다.")
        self.tts_audio.volume = volume / 100
        await ctx.reply(f"✅ TTS 볼륨을 `{volume}`%로 설정했어요.")

    @dico_command.on("message_create")
    async def on_tts_message(self, message: dico.Message):
        if message.author.bot or not self.tts_channel_id or message.channel_id != self.tts_channel_id:
            return
        tts = await generate_tts(message.content, loop=self.bot.loop)
        if tts:
            self.tts_audio.addTrack(dico_extsource.PyAVSource(tts, AVOption={"mode": "r"}))


def load(bot):
    bot.load_addons(TTS)


def unload(bot):
    bot.unload_addons(TTS)
