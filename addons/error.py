import traceback

import dico_command


class Error(dico_command.Addon):
    @dico_command.on("command_error")
    async def on_command_error(self, ctx: dico_command.Context, ex: Exception):
        if isinstance(ex, dico_command.InvalidArgument):
            await ctx.reply("❌ 인자값이 잘못되었습니다.")
        elif isinstance(ex, dico_command.CheckFailed):
            await ctx.reply("❌ 권한이 없습니다.")
        else:
            tb = "".join(traceback.format_exception(type(ex), ex, ex.__traceback__))
            edited_tb = ("..." + tb[-1985:]) if len(tb) > 2000 else tb
            await ctx.reply(f"```py\n{edited_tb}\n```")


def load(bot: dico_command.Bot):
    bot.load_addons(Error)


def unload(bot: dico_command.Bot):
    bot.unload_addons(Error)
