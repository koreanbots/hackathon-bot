import dico_command
import dico_interaction


class TTS(dico_command.Addon):
    @dico_interaction.command("tts")
    async def tts(self, ctx: dico_command.Context):
        pass


def load(bot):
    bot.load_addons(TTS)


def unload(bot):
    bot.unload_addons(TTS)
