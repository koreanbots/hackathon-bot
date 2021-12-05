import dico_command
import dico_interaction


class Vote(dico_command.Addon):
    @dico_interaction.component_callback("vote")  # Custom ID starts with "vote"
    async def vote_callback(self, ctx: dico_interaction.InteractionContext):
        pass

    @dico_command.command("vote")
    async def vote(self, ctx: dico_command.Context):
        pass

    @vote.subcommand("start")
    async def vote_start(self, ctx: dico_command.Context):
        pass


def load(bot):
    bot.load_addons(Vote)


def unload(bot):
    bot.unload_addons(Vote)
