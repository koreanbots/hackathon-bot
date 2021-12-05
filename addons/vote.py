import dico_command
import dico_interaction


class Vote(dico_command.Addon):
    @dico_interaction.component_callback("vote")
    async def vote_callback(self, ctx: dico_interaction.InteractionContext):
        pass

    @dico_interaction.command("vote")
    async def vote(self, ctx: dico_command.Context):
        pass

    @vote.command("start")
    async def vote_start(self, ctx: dico_command.Context):
        pass


def load(bot):
    bot.load_addons(Vote)


def unload(bot):
    bot.unload_addons(Vote)
