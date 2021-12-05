import dico_command
import dico_interaction


class Music(dico_command.Addon):
    @dico_command.command("play")
    async def play(self, ctx: dico_command.Context, *, query: str):
        pass

    @dico_command.command("volume")
    async def volume(self, ctx, volume: int = None):
        pass


def load(bot):
    bot.load_addons(Music)


def unload(bot):
    bot.unload_addons(Music)
