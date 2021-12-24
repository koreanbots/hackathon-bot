import dico_command


class Utils(dico_command.Addon):
    @dico_command.command("초대")
    async def invite(self, ctx: dico_command.Context, bot_id: int, slash: str = None):
        oauth2 = f"https://discord.com/api/oauth2/authorize?client_id={bot_id}&permissions=0&scope=bot"
        if slash:
            oauth2 += "%20applications.commands"
        await ctx.reply(oauth2)


def load(bot: dico_command.Bot):
    bot.load_addons(Utils)


def unload(bot: dico_command.Bot):
    bot.unload_addons(Utils)
