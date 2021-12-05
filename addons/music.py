import dico_command
import dico_interaction


class Music(dico_command.Addon):
    @dico_interaction.command("play")
    async def play(self, ctx: dico_command.Context, *, query: str):
        pass


def load(bot):
    bot.load_addons(Music)


def unload(bot):
    bot.unload_addons(Music)
