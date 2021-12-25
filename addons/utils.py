import dico
import dico_command

from config import Config


class Utils(dico_command.Addon):
    @dico_command.command("초대")
    async def invite(self, ctx: dico_command.Context, bot_id: int, slash: str = None):
        oauth2 = f"https://discord.com/api/oauth2/authorize?client_id={bot_id}&permissions=0&scope=bot"
        if slash:
            oauth2 += "%20applications.commands"
        oauth2 += "&guild_id=911676954317582368"
        await ctx.reply(oauth2)

    @dico_command.on("message_create")
    async def on_message(self, message: dico.Message):
        if message.channel_id != Config.IMAGE_CHANNEL_ID or not message.attachments:
            return
        await message.create_reaction("⭐")

    @dico_command.command("close")
    async def close(self, ctx: dico_command.Context):
        await ctx.reply("아이디어톤과 메이크톤 중 하나를 선택해주세요.")

    @close.subcommand("아이디어톤")
    async def close_idea(self, ctx: dico_command.Context):
        for channel in await self.bot.request_guild_channels(ctx.guild_id):
            if channel.name == Config.IDEATHON_NAME:
                parent = self.bot.get_channel(channel.parent_id)
                if parent.name in Config.EXCLUDE_CATEGORIES:
                    continue
                ow = [
                    n
                    for n in channel.permission_overwrites
                    if n.id != ctx.guild_id and n.id != Config.TEAM_ROLE
                ][0]
                ow.edit(send_messages=False)
                await channel.edit_permissions(ow, reason="아이디어톤 종료")
        await ctx.reply("✅ 아이디어톤을 종료했습니다.")

    @close.subcommand("메이크톤")
    async def close_idea(self, ctx: dico_command.Context):
        for channel in await self.bot.request_guild_channels(ctx.guild_id):
            if channel.name == Config.MAKETHON_NAME:
                parent = self.bot.get_channel(channel.parent_id)
                if parent.name in Config.EXCLUDE_CATEGORIES:
                    continue
                ow = [
                    n
                    for n in channel.permission_overwrites
                    if n.id != ctx.guild_id and n.id != Config.TEAM_ROLE
                ][0]
                ow.edit(send_messages=False)
                await channel.edit_permissions(ow, reason="메이크톤 종료")
        await ctx.reply("✅ 메이크톤을 종료했습니다.")


def load(bot: dico_command.Bot):
    bot.load_addons(Utils)


def unload(bot: dico_command.Bot):
    bot.unload_addons(Utils)
